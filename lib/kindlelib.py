# encoding: utf-8

import os
import sys
import ctypes

PY3 = sys.version_info[0] == 3

def isKindleDisk(disk):
    path = os.path.join(disk, 'system\\version.txt')
    if os.path.isfile(path):
        with open(path) as f:
            text = f.read()
            return text.startswith('Kindle')

def findKindleDisk():
    """ 自动查找 kindle 盘符 """
    lpBuffer = ctypes.create_string_buffer(78)
    ctypes.windll.kernel32.GetLogicalDriveStringsA(ctypes.sizeof(lpBuffer), lpBuffer)
    raw = lpBuffer.raw
    if PY3:
        raw = raw.decode('utf-8')
    vol = raw.split('\x00')
    for disk in vol:
        if disk and isKindleDisk(disk):
            return disk