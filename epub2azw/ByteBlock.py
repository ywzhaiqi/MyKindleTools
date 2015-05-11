#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct
import string
import utils
from MobiFormat import value_mapper, header_len, he_count, he_len, he_name, he_type, NONE_OFFSET

class ByteBlockError(Exception):
    pass

class ByteBlock:
    def __init__(self, data, offset=0, length=-1, name='', vt=None):
        self.data = data
        self.max_offset = len(self.data)
        # offset 的最大位数
        self.ow_h = str(utils.int_bits(self.max_offset, 'h')) # 十六进制
        self.ow_d = str(utils.int_bits(self.max_offset))      # 十进制
        #
        self.offset = offset
        if length < 0:
            self.length = len(data)
        else:
            self.length = length
        # 检查 self.offset、 self.length 的合法性
        #if self.offset < 0:
        #    raise
        self.name = name
        self.vt = vt
        self.descs = []
        self.is_exth_mdata = False
        self.dv = False
        #
        #self.is_solid = False
        self.sdata = None
        #
        self.sects = []

    def tail_offset(self):
        return self.offset + self.length

    def offset_is_valid(self, offset):
        return offset >= self.offset and offset < self.tail_offset()

    def sect_count(self):
        '''返回划分的区段数。'''
        return len(self.sects)

    def sect(self, sect_id):
        '''返回指定的区段。'''
        if isinstance(sect_id, int):
            return self.sects[sect_id]
        else:
            for sect in self.sects:
                if sect.name == sect_id:
                    return sect

    def sect_value(self, sect_id):
        '''如果指定的区段存在，返回其值；如果不存在，返回 None。'''
        s = self.sect(sect_id)
        if s is not None:
            return s.value()

    def cut(self, offset, name=['', ''], vt=['', '']):
        '''在指定偏移量的位置剖分区段。'''
        if self.offset_is_valid(offset):
            if self.sect_count() == 0:
                self.sects.append(ByteBlock(self.data, self.offset, offset - self.offset, name[0], vt[0]))
                self.sects.append(ByteBlock(self.data, offset, self.tail_offset() - offset, name[1], vt[1]))
                return 0
            else:
                for i in range(self.sect_count()):
                    sect = self.sect(i)
                    if sect.offset_is_valid(offset):
                        offset_tail = sect.tail_offset()
                        sect.length = offset - sect.offset
                        if name[0] != None: sect.name = name[0]
                        if vt[0] != None: sect.vt = vt[0]
                        sect_cutoff = ByteBlock(self.data, offset, offset_tail-offset, name[1], vt[1])
                        self.sects.insert(i+1, sect_cutoff)
                        return i
                        break
        else:
            raise('Invalid offset.')

    def split_last_sect(self, length, name='', vt=None):
        '''剖分最后一个区段。'''
        if self.sect_count() == 0:
            offset_start = self.offset
            name_old = 'Unparsed'
            vt_old = None
        else:
            sect = self.sect(-1)
            if length >= sect.length: # 不需要剖分
                sect.name = name
                sect.vt = vt
                sect.dv = True
                return sect
            offset_start = sect.offset
            name_old = sect.name
            vt_old = sect.vt
        offset = offset_start + length
        sect_id = self.cut(offset, name=[name, name_old], vt=[vt, vt_old])
        self.sect(sect_id).dv = True
        return self.sect(sect_id)

    def parse_header(self, hf, name='Header'):
        header = self.split_last_sect(header_len(hf), name)
        for i in range(he_count(hf)):
            header.split_last_sect(he_len(hf, i), name=he_name(hf, i), vt=he_type(hf, i))
        #header.sects[-1].name = he_name(hf, he_count(hf)-1)
        #header.sects[-1].vt = he_type(hf, he_count(hf)-1)
        return header

    def add_desc(self, descs):
        for desc in descs:
            if not desc in self.descs:
                self.descs.append(desc)

    def value(self):
        if self.is_exth_mdata:
            # EXTH mdata entry 除去前 8 个字节才是其值
            data = self.data[self.offset+8:self.tail_offset()]
        else:
            data = self.data[self.offset:self.tail_offset()]
        #
        if self.vt in ('i', 'x', 't', 'f'):
            return utils.unpack_int(data)
        else:
            return data

    def _printable_data(self):
        data = self.data[self.offset:self.tail_offset()]
        # 判断 data 是否全由可打印字符组成
        for c in data:
            if not c in string.printable:
                return "b'" + data.encode('hex') + "'"
        #
        return data

    def dump_offset(self):
        s = '0x{0:0' + self.ow_h + 'x}:0x{1:0' + self.ow_h + 'x}({2:0' + self.ow_d + 'd})'
        return s.format(self.offset,
                        self.tail_offset(),
                        self.length)

    def dump_name(self):
        w = 20
        if self.is_exth_mdata: w = 30
        s = '{0:' + str(w) + 's}'
        return s.format(self.name)

    def dump_value(self):
        v = self.value()
        if self.vt == 'i':
            desc = ''
            if self.name in value_mapper:
                desc = '(' + value_mapper[self.name][v] + ')'
            return '{0:d}'.format(v) + desc
        elif self.vt == 'x':
            return '0x{0:x}'.format(v)
        elif self.vt == 't':
            return str(utils.time_formatter(v))
        elif self.vt == 'f':
            if v == 0xffffffff:
                return '0xffffffff'
            else:
                return '{0:d}'.format(v)
        elif self.vt == 'h':
            return "h'" + v.encode('hex') + "'"
        elif self.vt == 's':
            return v.rstrip('\x00')
        else: # 默认为 'r'
            return v

    def dump_desc(self):
        s = ''
        #if self.descs != None:
        for desc in self.descs:
            s = s + '[' + desc + ']'
        return s

    def dump(self, level=0):
        #print 'dumping', self.name # dump 失败时用于调试
        s = '  '*level + self.dump_offset() + '  ' + self.dump_name()
        if self.sect_count() == 0 and self.dv:
            s = s + '  ' + self.dump_value()
        desc = self.dump_desc()
        if len(desc) > 0:
            s = s + '  ' + desc
        s = s +  '\n'
        for sect in self.sects:
            #print sect.name
            s = s + sect.dump(level+1)
        return s

    def raw_data(self):
        return self.data[self.offset:self.tail_offset()]

    def export(self, filename):
        f = open(filename, 'wb')
        f.write(self.raw_data())
        f.close()

    def solidify_data(self):
        if self.sect_count() == 0: # 基本区段
            if self.sdata == None:
                self.sdata = self.raw_data()
        else: # 包含子区段
            for sect in self.sects:
                ByteBlock.solidify_data(sect)

    def set_value(self, v):
        if self.sdata == None:
            raise ByteBlockError('The byte block is not solified.')
        if self.vt in ['i', 'x', 'f']:
            if self.is_exth_mdata:
                self.sdata = self.sdata[:8] + utils.pack_int(v, self.length-8)
            else:
                if self.value() != NONE_OFFSET:
                    self.sdata = utils.pack_int(v, self.length)
        else:
            raise ByteBlockError('Only integer value can be set.')

    def add_value(self, v):
        self.set_value(self.value()+v)

    def export_sdata(self, f):
        if self.sect_count() == 0: # 基本区段
            f.write(self.sdata)
        else: # 包含子区段
            for sect in self.sects:
                sect.export_sdata(f)
