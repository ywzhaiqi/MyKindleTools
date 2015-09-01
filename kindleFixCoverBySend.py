# encoding: utf-8

# 补全推送 mobi 缺失的封面

import os
import glob
import re
from io import BytesIO
from PIL import Image
from lib.kindlelib import findKindleDisk
from kindleunpack.mobi_sectioner import Sectionizer
from kindleunpack.mobi_header import MobiHeader


# 封面缩略图的最大分辨率
THUMB_MAX_SIZE = (220, 330) # Kindle Paper White

SET_COVER_BY_MANUAL = True


def findCoverFromImg(kb):
    ''' 尝试从图片中找出封面
    '''
    # Frontcover.jpg

def getCoverImage(fileOrPath, doctype='PDOC'):
    try:
        cover = Image.open(fileOrPath).convert('RGB')
        cover.thumbnail(THUMB_MAX_SIZE)
        # cover.thumbnail((283, 415), Image.ANTIALIAS)

        if doctype == 'PDOC':
            pdoc_cover = Image.new("L", (cover.size[0], cover.size[1]+55),
                                   "white")
            pdoc_cover.paste(cover, (0, 0))
            return pdoc_cover
        else:
            return cover
    except:
        print('Convert cover Error: %s' % thumbPath)

def getCoverByManual(filePath):
    azw3_name = os.path.basename(filePath)

    imgPath = None
    try:
        imgPath = input('Cover path of %s: ' % azw3_name)
    except:
        # print('请加上引号')
        pass

    cover = None
    if imgPath and os.path.isfile(imgPath):
        cover = getCoverImage(imgPath)

    return cover

def saveThumbnail(filePath, thumbPath):
    # 移除 .partial结尾的缺失图片
    partialPath = '%s.partial' % thumbPath
    if os.path.isfile(partialPath):
        os.remove(partialPath)

    sect = Sectionizer(filePath.decode('mbcs').encode('utf-8'))
    if sect.ident != 'BOOKMOBI' and sect.ident != 'TEXtREAd':
        return

    mh = MobiHeader(sect,0)
    metadata = mh.getMetaData()

    cover = None

    # get cover data
    beg = mh.firstresource
    cover_offset = int(metadata.get('CoverOffset', ['-1'])[0])
    if cover_offset != -1:
        data = sect.loadSection(beg + cover_offset)
        cover = getCoverImage(BytesIO(data))

    if not cover and SET_COVER_BY_MANUAL:
        cover = getCoverByManual(filePath)

    if cover:
        cover.save(thumbPath)
        print('Saved thumbnail: %s' % thumbPath)
    
    print('')

def findNoThumbnailBook():
    pattern = re.compile(r'_([a-zA-Z1-9]{32})')

    for filePath in glob.glob('documents\\*.azw3') + glob.glob('documents\\*.azw'):
        filename = os.path.basename(filePath)
        match = pattern.search(filename)
        if match:
            thumbPath = 'system\\thumbnails\\thumbnail_%s_PDOC_portrait.jpg' % match.group(1)
            if not os.path.isfile(thumbPath):
                saveThumbnail(filePath, thumbPath)

def main():
    print(u"功能：补全推送 mobi 缺失的封面（kindlegen生成的 mobi）")
    disk = findKindleDisk()
    if disk:
        os.chdir(disk)
        findNoThumbnailBook()
    else:
        print(u'请插入 kindle 设备')

    raw_input(u'全部完成，按回车键退出：'.encode('gbk'))

if __name__ == '__main__':
    main()
