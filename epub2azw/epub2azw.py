#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 将电子书从 epub 格式转换为 azw3 格式。

import os
import sys
import glob
import codecs
import subprocess
import tempfile
import shutil
#
import utils
import KindleEBook

# 命令行还有 bug，路径中包含 • 字符时会报错

def strOf(s):
    return s.decode('utf-8').encode(sys.stdin.encoding)

class Epub2AzwError(Exception):
    pass

def mobiToAzw3():
    pass

def main():
    cmd_kindlegen = 'kindlegen'
    try:
        s = subprocess.check_output(cmd_kindlegen)
    except:
        raise Epub2AzwError(cmd_kindlegen + ' not found.')
    # 判断是否有命令行路径
    epubFiles = None
    if len(sys.argv) > 1:
        epubFiles = sys.argv[1:]
        # 如果当前目录不是文件的父目录，则修正下
        if os.path.isabs(epubFiles[0]):
            os.chdir(os.path.dirname(epubFiles[0]))
    else:
        epubFiles = glob.glob('*.epub')

    cwd = os.getcwd()

    # 生成并处理
    for epub_file in epubFiles:
        print 'Processing ' + epub_file + ':'

        basename, ext = os.path.splitext(epub_file)
        basename = os.path.basename(basename)
        mobi_file = basename + '.mobi'
        azw3_file = basename + '.azw3'
        

        isMobi = ext == '.mobi'

        # 从 epub 文件的元数据里获取 ASIN
        # <dc:identifier opf:scheme="ASIN">B00ABCDEFG</dc:identifier>
        asin = '' if isMobi else utils.identifier_asin(epub_file)
        #print 'ASIN:', asin
        #raise SyntaxError

        if not isMobi:
            # 调用 Kindlegen 将电子书从 epub 格式转换为 MOBI KF6&8 格式
            cmd_epub2mobi = cmd_kindlegen + ' "' + epub_file + '" -o "' + mobi_file + '" -c1'
            try:
                s = subprocess.check_output(cmd_epub2mobi, 
                                            stderr=subprocess.STDOUT, # 将进程的 STDERR 输出合并到 STDOUT
                                            shell=True)
            except subprocess.CalledProcessError as e:
                print e.output.decode('utf-8', 'replace').encode('mbcs', 'replace')
                # #
                # if os.path.isfile(mobi_file):
                #     s = raw_input('Kindlegen returned with non-zero exit code. But ' + mobi_file + ' has already been generated. Do you want to continue?(y/n): ')
                #     if s != 'y' and s != 'Y':
                #         raise
            else:
                print s.decode('utf-8', 'replace').encode('mbcs', 'replace')

            # 在当前目录下，创建临时工作目录，并将 Kindlegen 生成的 MOBI KF6&8
            # 格式电子书移到该临时工作目录下
            
            if not os.path.isfile(os.path.realpath(mobi_file)):
                raw_input(strOf('有错误发生，请输入 Enter 键退出'))
                sys.exit(2)
            
            workspace_path = tempfile.mkdtemp(dir=cwd) # 临时工作目录绝对路径
            
            shutil.move(mobi_file, workspace_path)
            os.chdir(workspace_path)
            shutil.rmtree(workspace_path)

        # 从 MOBI KF6&8 格式电子书里提取 KF8 格式 AZW3 电子书；
        # 添加 EXTH metadata 501/CDEContentType: EBOK；
        # 替换封面缩略图。
        KindleEBook.extract_kf8(mobi_file.decode('mbcs'), asin, 'none')

        des = os.path.join(cwd, azw3_file)
        if os.path.isfile(des):
            os.remove(des)
        shutil.move(azw3_file, cwd)
        os.chdir(cwd)
        

if __name__ == '__main__':
    main()