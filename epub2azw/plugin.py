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
import re
import Tkinter as tkinter
import tkFileDialog
#
import epub2azw_opt
import utils
import KindleEBook

class Epub2AzwError(Exception):
    pass

def fileChooser(dialog_title):
    localRoot = tkinter.Tk()
    localRoot.withdraw()
    filename = tkFileDialog.askopenfilename(title=dialog_title)
    #localRoot.desdroy()
    return filename

def fileSaveAs(dialog_title):
    localRoot = tkinter.Tk()
    localRoot.withdraw()
    filename = tkFileDialog.asksaveasfilename(title=dialog_title)
    return filename

def mv_file(src_path, des_path):
    '''移动文件。

    当 des_path 已存在时，自动覆盖该文件。
    '''
    if not os.path.isfile(src_path):
        return False
    if os.path.isfile(des_path):
        os.remove(des_path)
    shutil.move(src_path, des_path)
    return True

# 获取 KindleGen 可执行文件路径
def get_cmd_kindlegen():
    # 首先不带路径执行命令 kindlegen，看是否成功
    cmd_kindlegen = 'kindlegen'
    try:
        s = subprocess.check_output(cmd_kindlegen)
    except:
        # 由用户指定 kindlegen 路径
        cmd_kindlegen = fileChooser("Find command kindlegen")
        if cmd_kindlegen is None:
            raise Epub2AzwError('Failed to locate kindlegen.')
        pass
    return cmd_kindlegen

def get_book_asin(bk):
    '''从 epub 文件的元数据里获取 ASIN。

    如果无法获取 ASIN，返回 None。
    '''
    metadata = bk.getmetadataxml()
    # <dc:identifier opf:scheme="ASIN">B00ABCDEFG</dc:identifier>
    match_asin = re.search('<dc:identifier opf:scheme="ASIN">([^>]+)</dc:identifier>', metadata)
    if not match_asin:
        print 'Info: ASIN not found in the metadata of the epub file.'
        return None
    asin = str(match_asin.group(1))
    if not re.match('B00[0-9A-Z]{7}', asin):
        print 'Warning: "' + asin + '"', 'seems not like a valid ASIN.'
    return asin

def get_book_title(bk):
    metadata = bk.getmetadataxml()
    match_title = re.search('<dc:title>([^>]+)</dc:title>', metadata)
    if not match_title:
        return None
    return unicode(match_title.group(1))

# 如果当前目录里存在相同标题的 epub 文件，则返回其文件名；
# 否则弹出对话框让用户选择文件名。
def get_filename(current_title, cwd):
    cwd = cwd.encode('mbcs')
    for epub_file in glob.glob('*.epub'):
        title = utils.get_epub_title(epub_file) # 从 epub 文件的元数据里获取标题
        #print 'epub_file:', epub_file, title
        if title == current_title:
            basename, ext = os.path.splitext(epub_file)
            return os.path.join(cwd, basename + '.azw3')
    # 当前目录下没有 epub 文件与 Sigil 当前编辑的文件标题相同
    filename = fileSaveAs('Save generated azw3 file as')
    return filename

def kindlegen_output_formatter(s):
    s1 = s.replace('\r\r\n', '\n')
    return s1.replace('\r\n', '\n')

##############################
#
# Sigil 插件入口
#
##############################

def run(bk):
    opts = epub2azw_opt.epub2azw_opt() # epub2azw 选项
    if opts.sv_popup.get():
        opts.set()

    cmd_kindlegen = get_cmd_kindlegen()

    cwd = os.getcwd().decode('mbcs')

    # 在当前目录下，创建临时工作目录
    workspace_path = tempfile.mkdtemp(dir=cwd) # 临时工作目录绝对路径
    os.chdir(workspace_path)
    # 
    bk.copy_book_contents_to(workspace_path)
    opf_path = os.path.join(workspace_path, 'OEBPS', 'content.opf')
    # 调用 Kindlegen 将电子书从 epub 格式转换为 MOBI KF6&8 格式
    cmd_epub2mobi = cmd_kindlegen + ' ' + opts.kindlegen() + ' "' + opf_path + '"'
    try:
        s = subprocess.check_output(cmd_epub2mobi.encode('mbcs'),
                                    stderr=subprocess.STDOUT, # 将进程的 STDERR 输出合并到 STDOUT
                                    shell=True)
    except subprocess.CalledProcessError as e:
        print kindlegen_output_formatter(e.output)
    else:
        print kindlegen_output_formatter(s)

    mobi_path = os.path.join(workspace_path, 'OEBPS', 'content.mobi')
    if not os.path.isfile(mobi_path):
        print 'KindleGen failed to generate', mobi_path
        return -1

    asin = get_book_asin(bk)
    # 从 MOBI KF6&8 格式电子书里提取 KF8 格式 AZW3 电子书
    #
    # 添加 EXTH metadata：
    #   (1) 501/CDEContentType = EBOK
    #   (2) 113/ASIN, 504/ASIN
    #
    # 替换封面缩略图
    pseudo_asin = KindleEBook.extract_kf8(mobi_path, asin, opts.thumbnail())
    if asin is None:
        asin = pseudo_asin

    os.chdir(cwd.encode('mbcs'))
    azw_path = os.path.join(workspace_path, 'OEBPS', 'content.azw3')
    current_title = get_book_title(bk)
    #print 'current_title:', current_title
    des_path = get_filename(current_title, cwd)
    # 移动 azw 文件
    mv_file(azw_path, des_path)
    # 移动封面缩略图，要求 ASIN 非 None
    if asin is not None and opts.thumbnail() != 'none':
        print 'Outputing cover thumbnail...'
        src_path = os.path.join(workspace_path, 'thumbnail.jpg')
        des_path = os.path.join(cwd, 'thumbnail_' + asin + '_EBOK_portrait.jpg')
        mv_file(src_path, des_path)
        print 'Done'
    # 删除临时工作目录
    shutil.rmtree(workspace_path.encode('mbcs'))

    return 0
