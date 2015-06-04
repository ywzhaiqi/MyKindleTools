# python3
import sys
import os
import shutil
from lib.kindlelib import findKindleDisk

includeExts = ['.mobi', '.azw', '.azw3', '.azw4', '.pdf', '.txt', '.prc', '.pobi', '.epub']
excludeDirs = ['dictionaries']

stdout_encoding = sys.stdout.encoding

def clean(workDir):
    outDirs = []
    count = 0
    for root, dirs, files in os.walk(workDir):
        # 取得所有存在的电子书名称（noExt）
        allFiles = []
        for file in files:
            fileName, ext = os.path.splitext(file)
            if ext in includeExts:
                allFiles.append(fileName)

        for dir in dirs:
            if not '.sdr' in dir:
                continue
            if dir in excludeDirs:
                continue
            if dir[:-4] in allFiles:  # 检验是否存在
                continue

            # 删除文件夹（可能非空）
            dirPath = os.path.join(root, dir)
            shutil.rmtree(dirPath)
            
            # 当路径存在 gbk 不支持的字符时，print 就会错误
            print('removed: %s' % dirPath.encode(stdout_encoding, 'replace').decode(stdout_encoding))
            count += 1

            # # 删除空文件夹
            # if '.sdr' in dir:
            #     continue
            # if not os.listdir(dirPath):
            #     os.rmdir(dirPath)

    if count:
        print('共删除 %s 个不存在的 sdr 文件夹' % count)
    else:
        print('没有需要删除的 sdr 文件夹')

def main():
    disk = findKindleDisk()
    if disk:
        documentDir = os.path.join(disk, 'documents')
        clean(documentDir)

if __name__ == '__main__':
    main()
