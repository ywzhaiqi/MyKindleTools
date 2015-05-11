#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct
import imghdr
from PIL import Image
import StringIO
import sys
import os
#
from ByteBlock import ByteBlock
from MobiFormat import pdb_header_format, ior_format, PalmDOC_header_format, kf8_header_format, exth_header_format, exth_mdata_format, guess_types, MOBI_HEADER_LEN, NONE_OFFSET, header_len, he_type, exth_mdata_name, THUMB_MAX_SIZE_KPW, THUMB_MAX_SIZE_KV
import utils

THUMB_MAX_SIZE = THUMB_MAX_SIZE_KPW

class KEBError(Exception):
    #def __init__(self, msg):
    #    self.msg = msg
    #def __str__(self):
    #    return msg
    pass

class KindleEBook(ByteBlock):
    def __init__(self, filename=None, data=None):
        if filename != None:
            data = open(filename.encode('mbcs'), 'rb').read()
            name = filename.encode('utf-8')
        else:
            name = 'Generated from data'
        ByteBlock.__init__(self, data, name=name, vt=None)
        #self._offset_unparsed = 0 # 未解析部分的起始位置
        self.kf_format = 'Unknown'
        self.pseudo_asin = None
        self._parse()

    def _parse(self):
        # PDB Header
        pdb_header = self.parse_header(pdb_header_format, 'PDB Header')
        sect = pdb_header.sect('record_count')
        self.rec_count = sect.value()
        #print 'record count:', self.rec_count
        # Info of Records
        self._parse_info_of_records(self.rec_count)
        # Gap
        gap = self.split_last_sect(2, name='Gap', vt='i')
        if gap.value() != 0:
            raise KEBError('Gap bytes are not null.')
        gap.dv = False
        # Records
        if self.sect(-1).offset != self.offset_of_records[0]:
            raise KEBError('Invalid offset of record #0.')
        self.sect_id_of_first_record = self.sect_count() - 1 # 记录的起始区段编号
        for i in range(self.rec_count):
            length = self.offset_of_records[i+1] - self.offset_of_records[i]
            record = self.split_last_sect(length, 'Record #{0}'.format(i))
            record.dv = False
            record.descs = []
            if i == 0:
                self._parse_header_record(record) # 解析 HEADER 记录
                # 确定 MOBI 文件格式： 'KF6'、 'KF8'、 'KF6&8'
                self.second_header_rec_id = None
                if self.is_kf8_header(record):
                    self.kf_format = 'KF8'
                else:
                    rec_id = self.exth_mdata(121)
                    if not rec_id in [None, NONE_OFFSET]: # EXTH mdata 121 存在，且值不等于 0xffffffff
                        self.second_header_rec_id = rec_id
                        self.kf_format = 'KF6&8'
                    else:
                        self.kf_format = 'KF6'
            else:
                self._guess_record_type(record) # 根据记录起始若干字节的内容，确定记录类型
        # 根据 MOBI Header 和 EXTH Header 的内容，进一步确定记录类型
        self._determine_record_type(0)
        if self.kf_format == 'KF6&8':
            if self.record(self.second_header_rec_id-1).descs[0] != 'BOUNDARY':
                raise KEBError('Invalid second header record id.')
        if self.second_header_rec_id != None:
            header_rec = self.record(self.second_header_rec_id)
            self._parse_header_record(header_rec) # 解析第二条 HEADER 记录
            self._determine_record_type(self.second_header_rec_id)

    def _parse_info_of_records(self, rec_count):
        self.offset_of_records = [] # 各记录的偏移量
        for i in range(rec_count):
            ior = self.parse_header(ior_format, 'Info of Record #{0}'.format(i))
            self.offset_of_records.append(ior.sect('record_offset').value())
        self.offset_of_records.append(self.length)

    def record(self, rec_id):
        if rec_id < 0 or rec_id > self.rec_count - 1:
            raise KEBError('Invalid record id.')
        return self.sect(self.sect_id_of_first_record + rec_id)

    def is_kf8_header(self, record):
        if len(record.descs) > 1:
            if record.descs[0] == 'HEADER' and record.descs[1] == 'KF8':
                return True
        return False

    # 如果有多个条目
    def exth_mdata_entry(self, mdata_id, rec_id=0):
        if rec_id != 0:
            rec_id = self.second_header_rec_id
        header_record = self.record(rec_id)
        name = exth_mdata_name(mdata_id)
        for i in range(3, header_record.sect_count()):
            mdata = header_record.sect(i)
            if mdata.name == name:
                return mdata

    # 可调用 exth_mdata_entry()
    def exth_mdata(self, mdata_id, rec_id=0):
        '''读取 EXTH 元数据'''
        if rec_id != 0:
            #raise KEBError('Header record other than 0 not supported yet.')
            rec_id = self.second_header_rec_id
        header_record = self.record(rec_id)
        s = str(mdata_id) + '('
        for i in range(3, header_record.sect_count()):
            mdata = header_record.sect(i)
            if mdata.name.startswith(s):
                return mdata.value()
        return None

    def _parse_header_record(self, record):
        '''解析 header 记录'''
        record.descs.append('HEADER')
        # PalmDOC Header
        record.parse_header(PalmDOC_header_format, 'PalmDOC Header')
        # MOBI Header
        # MOBI Header 的长度似乎随版本有变化：
        # kindlegen 2.8 生成的文件为 0x100，
        # kindlegen 2.9 生成的文件为 0x108，多出两个 4 字节条目。
        mobi_header_len = self.mobi_header_len(record)
        #if not mobi_header_len in [0x100, 0x108]:
        #    raise KEBError('Unknown MOBI Header length encounted:', mobi_header_len)
        entry_count = 0
        for i in range(len(kf8_header_format)):
            if kf8_header_format[i][0] == mobi_header_len:
                entry_count = i
                break
        mobi_header = record.parse_header(kf8_header_format[:entry_count+1], 'MOBI Header')
        #
        title_offset = mobi_header.sect('title_offset').value() + record.offset
        title_length = mobi_header.sect('title_length').value()
        if mobi_header.sect('mobi_identifier').value() != 'MOBI':
            raise KEBError('Invalid MOBI Header.')
        #
        if mobi_header.sect('kf_version').value() == 5:
            record.descs.append('KF5')
        elif mobi_header.sect('kf_version').value() == 6:
            record.descs.append('KF6')
        elif mobi_header.sect('kf_version').value() == 8:
            record.descs.append('KF8')
        else:
            raise KEBError('Invalid kf_version entry in MOBI header.')
        # 校验 MOBI header 长度
        if mobi_header.sect('mobi_header_len').value() != mobi_header.length:
            print 'mobi header length wrong.'
        # EXTH block (EXTH Header + EXTH mdata)
        if mobi_header.sect('exth_flags').value() & 0x40:
            exth_header = record.parse_header(exth_header_format, 'EXTH Header')
            if exth_header.sect('exth_identifier').value() != 'EXTH':
                raise KEBError('Invalid EXTH Header.')
            self.exth_mdata_count = exth_header.sect('exth_mdata_count').value()
            exth_len = exth_header.sect('exth_length').value()
            sum_of_exth_len = 12 # EXTH Header 的长度
            for i in range(self.exth_mdata_count):
                #print 'exth mdata', i
                exth_mdata = self._parse_exth_mdata(record)
                sum_of_exth_len += exth_mdata.length
            # 校验 EXTH block 长度
            if sum_of_exth_len > exth_len:
                raise KEBError('Sum of EXTH length is', sum_of_exth_len, ', which is greater than', exth_len)
            #if sum_of_exth_len < exth_len:
            #    print 'Sum of EXTH length is', sum_of_exth_len, ', which is less than', exth_len
        # title
        offset = record.sect(-1).offset
        if title_offset < offset:
            raise KEBError('Invalid title_offset', title_offset, ', which is less than tail of EXTH block', offset)
        if title_offset > offset:
            #print 'There is padding between EXTH block and title.'
            data = self.data[offset:title_offset]
            for c in data:
                if c != '\x00':
                    #raise KEBError('Bytes between EXTH block and title are not null.')
                    print 'Warning: Bytes between EXTH block and title are not null.'
                    break
            pad = record.split_last_sect(title_offset-offset, name='Unparsed')
            pad.dv = False
        title = record.split_last_sect(title_length, name='Title', vt='s')

    def mobi_header_len(self, record):
        data = self.data[record.offset+0x14:record.offset+0x14+4]
        return utils.unpack_int(data)

    def _parse_exth_mdata(self, record):
        offset = record.sect(-1).offset
        length = utils.unpack_int(self.data[offset+4:offset+8])
        mtype = utils.unpack_int(self.data[offset:offset+4])
        #name = '{0:03d}({1})'.format(mtype, exth_mdata_format[mtype][1])
        name = exth_mdata_name(mtype)
        if mtype in exth_mdata_format:
            vtype = exth_mdata_format[mtype][0]
        else:
            vtype = 'h'
        mdata = record.split_last_sect(length, name=name, vt=vtype)
        mdata.is_exth_mdata = True
        return mdata

    def _guess_record_type(self, record):
        # 记录开头若干（12/8/4）字节的内容
        s_first_12 = record.data[record.offset:record.offset+12]
        s_first_8 = s_first_12[:8]
        s_first_4 = s_first_12[:4]
        if s_first_12 in guess_types:
            record.descs.append(guess_types[s_first_12])
        elif s_first_8 in guess_types:
            record.descs.append(guess_types[s_first_8])
        elif s_first_4 in guess_types:
            record.descs.append(guess_types[s_first_4])
        # 图像
        imgtype = imghdr.what(None, record.data[record.offset:record.tail_offset()])
        if imgtype != None:
            record.descs.append('IMAG')
            record.descs.append(imgtype)

    def _determine_record_type(self, head_rec_id):
        record  = self.record(head_rec_id)
        palmdoc_header = record.sect('PalmDOC Header')
        mobi_header = record.sect('MOBI Header')
        # TEXT 记录
        text_record_count = palmdoc_header.sect('text_rec_count').value()
        for i in range(text_record_count):
            text_record = self.record(head_rec_id + 1 + i)
            text_record.descs = ['TEXT']
        # INDX 记录
        self._determine_index_record(head_rec_id, 'ncx_index_ri', 'NCX') # NCX Index
        self._determine_index_record(head_rec_id, 'fragment_index_ri', 'Fragment') # Fragment Index
        self._determine_index_record(head_rec_id, 'skeleton_index_ri', 'Skeleton', 2) # Skeleton Index
        self._determine_index_record(head_rec_id, 'guide_index_ri', 'Guide') # Guide Index
        # HUFF 记录
        huff_count = mobi_header.sect('huff_count').value()
        if huff_count != 0:
            huff_offset = mobi_header.sect('huff_offset').value() + head_rec_id
            for i in range(huff_count):
                self.record(huff_offset+i).add_desc(['HUFF'])
        # huff_tbl 记录
        huff_tbl_count = mobi_header.sect('huff_tbl_count').value()
        if huff_tbl_count > 0:
            huff_tbl_offset = mobi_header.sect('huff_tbl_offset').value()
            for i in range(huff_tbl_count):
                self.record(head_rec_id+huff_tbl_offset+i).add_desc(['huff_tbl'])
        # SRCE 记录
        source_rec_id = mobi_header.sect('srcs_offset').value()
        source_rec_count = mobi_header.sect('srcs_count').value()
        for i in range(source_rec_count):
            self.record(source_rec_id+i).add_desc(['SOURCE'])
        # 图片
        first_image_record_id = -1
        for i in range(head_rec_id + 1, self.rec_count):
            if len(self.record(i).descs) > 0:
                if self.record(i).descs[0] == 'IMAG':
                    first_image_record_id = i
                    break
        # 封面、封面缩略图
        self.cover_rec_id = None
        self.thumb_rec_id = None
        if first_image_record_id > -1:
            # 封面
            cover_record_offset = record.sect_value('201(Cover_Offset)')
            if cover_record_offset is not None:
                self.cover_rec_id = first_image_record_id + cover_record_offset
                self.record(self.cover_rec_id).add_desc(['Cover'])
            # 封面缩略图
            thumb_record_offset = record.sect_value('202(Thumb_Offset)')
            if thumb_record_offset is not None:
                self.thumb_rec_id = first_image_record_id + thumb_record_offset
                self.record(self.thumb_rec_id).add_desc(['Cover Thumbnail'])

    def _determine_index_record(self, head_rec_id, key, des, count=3):
        mobi_header = self.record(head_rec_id).sect('MOBI Header')
        #index_rec_id = mobi_header.sect(key).value()
        sect = mobi_header.sect(key)
        if sect == None:
            return
        index_rec_id = sect.value()
        if index_rec_id != NONE_OFFSET:
            index_rec_id += head_rec_id
            self.record(index_rec_id).add_desc(['INDX', des + ' Index 0'])
            self.record(index_rec_id + 1).add_desc(['INDX', des + ' Index 1'])
            if count == 3:
                self.record(index_rec_id + 2).add_desc(['INDX', des + ' Index CNX'])

    def is_thumbnail_replacible(self):
        if self.thumb_rec_id is None:
            print 'No cover thumbnail to replace.'
            return False
        # 检查封面缩略图的尺寸
        data = self.record(self.thumb_rec_id).raw_data()
        thumb = Image.open(StringIO.StringIO(data))
        if not ( thumb.size[0] < THUMB_MAX_SIZE[0] and thumb.size[1] < THUMB_MAX_SIZE[1] ):
            #print 'and does not need replacing.'
            return False
        #
        if self.cover_rec_id is None:
            print 'No cover to generate thumbnail.'
            return False
        # 检查封面的尺寸
        data = self.record(self.cover_rec_id).raw_data()
        cover = Image.open(StringIO.StringIO(data))
        if cover.size[0] < THUMB_MAX_SIZE[0] and cover.size[1] < THUMB_MAX_SIZE[1]:
            #print 'and is too small for generating thumbnail.'
            return False
        return True

    def replace_thumbnail(self, new_book_filename):
        '''替换 AZW3 文件的封面缩略图为 THUMB_MAX_SIZE 像素。
        解决 AZW3 在 KPW 的封面视图（cover view）里封面缩略图偏小的问题。'''
        # 利用文件里的封面生成新的封面缩略图
        data = self.record(self.cover_rec_id).raw_data()
        cover = Image.open(StringIO.StringIO(data)).convert('RGB')
        cover.thumbnail(THUMB_MAX_SIZE)
        cover.save('thumbnail.jpg')
        new_thumb = open('thumbnail.jpg', 'rb').read()
        #print cover.format, cover.size, cover.mode
        #
        self.replace_record(self.thumb_rec_id, new_thumb, new_book_filename)

    def replace_record(self, rec_id, new_data, filename_new_book):
        rec_len = self.record(rec_id).length
        #print 'size of data:', rec_len, '->', len(new_data)
        rec_offset_inc = len(new_data) - rec_len # 记录长度增量，即后续记录偏离量增量
        #
        f = open(filename_new_book, 'wb')
        ior_next = self.sect(1+rec_id+1)
        f.write(self.data[:ior_next.offset]) # 第 rec_id+1 个 Info of Record 区段之前的内容保持不变
        # 从 rec_id+1 开始的 Info of Record 区段
        for i in range(rec_id+1, self.rec_count):
            ior = self.sect(i+1)
            data = ior.raw_data()
            rec_offset_new = ior.sect('record_offset').value() + rec_offset_inc
            s = struct.pack('>L', rec_offset_new)
            f.write(s)
            f.write(data[4:])
        # 从 Gap 到第 rec_id 条记录起始位置之间的内容保持不变
        offset_gap = self.sect('Gap').offset
        offset_rec = self.record(rec_id).offset
        f.write(self.data[offset_gap:offset_rec])
        # 新的第 rec_id 条记录
        f.write(new_data)
        # 第 rec_id+1 条记录及其后续内容保持不变
        offset = self.record(rec_id+1).offset
        f.write(self.data[offset:])
        f.close()

    def imag_resc_rec_ids(self):
        rec_ids = []
        for i in range(self.rec_count):
            if len(self.record(i).descs) >0:
                desc = self.record(i).descs[0]
                if desc in ['IMAG', 'RESC']:
                    # 检查 IMAG 和 RESC 记录是否连续
                    if len(rec_ids) > 0:
                        if i != rec_ids[-1] + 1:
                            raise KEBError('IMAG/RESC records are not continuous.')
                    rec_ids.append(i)
        return rec_ids

    def extract(self, filename, asin):
        '''从 KF6&8 格式文件里提取内容，保存为 KF8 格式文件。

        asin 为 None 表示未指定 ASIN； '' 表示需要人造 ASIN。
        '''
        if self.kf_format != 'KF6&8':
            raise KEBError("The input file's format is " + self.kf_format + '. Only mobi KF6&8 ebook supported.')
        f = open(filename, 'wb')
        #
        kf8_rec_count = self.rec_count - self.second_header_rec_id
        # 除了 IMAG 和 RESC 外， RESOURCE 不包括 HUFF 记录，因此不能使用 EXTH 125(resource_count)
        imag_resc_rec_ids = self.imag_resc_rec_ids()
        #print imag_resc_rec_ids
        imag_resc_rec_count = len(imag_resc_rec_ids)
        rec_count = kf8_rec_count + imag_resc_rec_count # KF8 文件的记录数
        kf8_header = self.record(self.second_header_rec_id).sect('MOBI Header')
        insert_offset = kf8_header.sect('first_resc_offset').value()
        # origin_rec_ids 为 KF8 文件各记录在原 KF6&8 文件里的记录编号的列表
        origin_rec_ids = range(self.second_header_rec_id, self.second_header_rec_id + insert_offset)
        for id in imag_resc_rec_ids:
            origin_rec_ids.append(id)
        for id in range(self.second_header_rec_id + insert_offset, self.rec_count):
            origin_rec_ids.append(id)
        #
        self.solidify_data()
        # PDB Header
        pdb_header = self.sect('PDB Header')
        # KF6&8 文件 BOUNDARY 记录的 record_unique_id 有跳动，导致 unique_id_seed = record_count * 2 + 1
        # 而对于 AZW3 文件， unique_id_seed = record_count * 2 - 1
        pdb_header.sect('unique_id_seed').set_value(rec_count * 2 - 1)
        pdb_header.sect('record_count').set_value(rec_count) # 修改文件记录数
        pdb_header.export_sdata(f)
        # IOR (Info Of Records)
        rec_offset = header_len(pdb_header_format) + 8 * rec_count + 2
        for i in range(rec_count):
            rec_id = origin_rec_ids[i]
            ior = self.sect(1+rec_id)
            ior.sect('record_offset').set_value(rec_offset)
            ior.sect('record_unique_id').set_value(2 * i)
            ior.export_sdata(f)
            rec_offset += self.record(rec_id).length
        # Gap
        self.sect('Gap').export_sdata(f)
        # MOBI Header
        mobi_header = self.record(self.second_header_rec_id).sect('MOBI Header')
        for name in ['last_con_record', 'fcis_record_id', 'flis_record_id', 'datp_record_id', 'gesw_offset']:
            mobi_header.sect(name).add_value(imag_resc_rec_count)
        # EXTH mdata
        # 125(resource_rec_count)
        #self.exth_mdata_entry(125, 1).add_value(imag_resc_rec_count)
        entry = self.exth_mdata_entry(125, 1)
        entry.add_value(imag_resc_rec_count)
        #
        mdata_to_add = []
        # 501(cdetype)
        if self.exth_mdata(501, 1) == None:
            mdata_to_add.append([501, 'EBOK'])
        else:
            raise KEBError('EXTH mdata 501(cdetype) already exist.')
        # 113/504(ASIN)
        # 人造 ASIN
        if asin == '':
            exth_mdata_542 = self.exth_mdata(542, 1)
            if exth_mdata_542 is None:
                exth_mdata_542 = ''
            asin = pdb_header.sect('pdb_name').dump_value() + exth_mdata_542
            asin = asin.upper()
            self.pseudo_asin = asin
        if asin is not None:
            mdata_to_add.append([113, asin])
            mdata_to_add.append([504, asin])
        print 'Adding EXTH metadata...'
        self.add_exth_mdata(mdata_to_add, 1)
        print 'Done'
        # 将各条记录写入文件
        for rec_id in origin_rec_ids:
            self.record(rec_id).export_sdata(f)
        f.close()

    def del_exth_mdata(self, mdata_ids, rec_id=0):
        if rec_id != 0:
            rec_id = self.second_header_rec_id
        header_record = self.record(rec_id)
        exth_header = header_record.sect('EXTH Header')
        exth_header_count = exth_header.sect('exth_mdata_count').value()
        sum_of_del_entry_len = 0
        for mdata_id in mdata_ids:
            print 'del', mdata_id
            exth_mdata_entry = self.exth_mdata_entry(mdata_id, rec_id)
            if exth_mdata_entry == None:
                print 'EXTH mdata', mdata_id, 'does not exist.'
            else:
                entry_len = exth_mdata_entry.length
                sum_of_del_entry_len += entry_len
                header_record.sects.remove(exth_mdata_entry) # 移除区段
                # 修改 EXTH Header
                exth_header_count += -1
                exth_header.sect('exth_mdata_count').set_value(exth_header_count)
        # 修改 EXTH Header 末尾的 null padding 的长度，增加字节 '\x00'
        # MOBI Header 里的 title_offset 保持不变
        pad = header_record.sect(3+exth_header_count)
        if pad.name == 'Unparsed':
            pad.sdata = pad.sdata + '\x00' * sum_of_del_entry_len
        else:
            raise KEBError('Need insert unparsed sect first.')

    # 在程序运行时只能调取一次
    # 输入时如果 rec_id != 0，则元数据写入第二 header 记录
    def add_exth_mdata(self, mdata_to_add, rec_id=0):
        if rec_id != 0:
            rec_id = self.second_header_rec_id
        header_record = self.record(rec_id)
        exth_header = header_record.sect(2)
        exth_mdata_count = exth_header.sect('exth_mdata_count').value()
        mdata_len = 0
        for mdata_pair in mdata_to_add:
            mdata_id = mdata_pair[0]
            value = mdata_pair[1]
            # virtual_exth_mdata 里仅 sdata 为有效内容
            virtual_exth_mdata = ByteBlock(self.data)
            mdata_type = exth_mdata_format[mdata_id][0]
            if mdata_type == 's':
                mdata_value_len = len(value)
                mdata = value
            else:
                raise KEBError('Only string EXTH mdata type implemented.')
            virtual_exth_mdata.sdata = utils.pack_int(mdata_id, 4) + utils.pack_int(mdata_value_len+8, 4) + mdata
            mdata_len += len(virtual_exth_mdata.sdata)
            header_record.sects.insert(3+exth_mdata_count, virtual_exth_mdata) # 插入到 EXTH mdata 列表末尾
        #
        exth_header.sect('exth_mdata_count').add_value(len(mdata_to_add)) # 修改 EXTH Header
        exth_header.sect('exth_length').add_value(mdata_len)
        # 修改 MOBI Header 里的 title_offset
        header_record.sect('MOBI Header').sect('title_offset').add_value(mdata_len)
        # 修改 title 之后的 null padding 的长度，去除末尾的 mdata_len 字节内容（被认为是 '\x00'）
        pad = header_record.sect(-1)
        pad.sdata = pad.sdata[:-mdata_len]

#
#
#

def dump_file(path):
    keb = KindleEBook(path)
    basename, ext = os.path.splitext(path)
    f = open(basename+'-dump.log', 'w')
    f.write(keb.dump())
    f.close()

def extract_kf8(path, asin, thumbnail):
    global THUMB_MAX_SIZE
    if thumbnail == 'kv': # 保留 KV 尺寸封面缩略图
        THUMB_MAX_SIZE = THUMB_MAX_SIZE_KV
    if thumbnail != 'none' and asin is None: # 为输出封面缩略图，需要生成 ASIN
        asin = ''
    #
    keb = KindleEBook(path)
    basename, ext = os.path.splitext(path)
    extracted_path = basename + '-temp.azw3'
    print 'Extracting KF8 ebook...'
    keb.extract(extracted_path, asin)
    pseudo_asin = keb.pseudo_asin
    #
    keb = KindleEBook(extracted_path)
    print 'Done'
    if keb.is_thumbnail_replacible():
        print 'Replacing the cover thumbnail...'
        keb.replace_thumbnail(basename+'.azw3')
        print 'Done'
    else:
        des = basename + '.azw3'
        if os.path.isfile(des):
            os.remove(des)
        os.rename(extracted_path, des)
    #
    return pseudo_asin

if __name__ == '__main__':
    print 'KindleEBook: Replacing the small cover thumbnail of Amazon KF8 ebook.'
    for p in sys.argv[1:]:
        basename, ext = os.path.splitext(p)
        if not ext.upper() in ('.AZW3', '.AZW'):
            raise KEBError('Only Amazon KF8 ebook supported.')
        print '\nProcessing ' + p + ':'
        print 'Parsing the file...'
        keb = KindleEBook(p)
        print 'Checking cover and cover thumbnail...'
        if keb.is_thumbnail_replacible():
            bak = basename+'-small.thumb'+ext
            os.rename(p, bak)
            print 'The original file has been saved as', bak
            print 'Replacing the cover thumbnail...'
            keb.replace_thumbnail(p)
            print 'Done'
