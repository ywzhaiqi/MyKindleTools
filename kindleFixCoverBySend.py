# encoding: utf-8

# 补全推送 mobi 缺失的封面

import os
import glob
import re
import StringIO
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

def setThumbnailByManual(filePath, thumbPath):
    azw3_name = os.path.basename(filePath)

    imgPath = None
    try:
        imgPath = input('Cover path of %s: ' % azw3_name)
    except:
        # print('请加上引号')
        pass

    if not imgPath:
        return False

    if not os.path.isfile(imgPath):
        print('The cover image is not correct, skipped')
    else:
        with open(imgPath, 'rb') as f:
            cover = Image.open(f).convert('RGB')
            cover.thumbnail(THUMB_MAX_SIZE)
            cover.save(thumbPath)

    return True

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

    isOK = False

    # get cover data
    beg = mh.firstresource
    cover_offset = int(metadata.get('CoverOffset', ['-1'])[0])
    if cover_offset != -1:
        data = sect.loadSection(beg + cover_offset)

        try:
            cover = Image.open(StringIO.StringIO(data)).convert('RGB')
            cover.thumbnail(THUMB_MAX_SIZE)
            cover.save(thumbPath)
            isOK = True
        except:
            print('Convert cover Error: %s' % thumbPath)

    if not isOK and SET_COVER_BY_MANUAL:
        isOK = setThumbnailByManual(filePath, thumbPath)

    if isOK:
        print('Saved thumbnail: %s' % thumbPath)
    
    print('')

def findNoThumbnailBook():
    pattern = re.compile(r'_([a-zA-Z1-9]{32})')

    for filePath in glob.glob('documents\\*.azw3'):
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
