#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import struct
import zipfile
from bs4 import BeautifulSoup
import re

class UtilsError(Exception):
    pass

def int_bits(v, base='d'):
    '''返回整数的位数。'''
    if base == 'd':
        b = 10
    elif base == 'h':
        b = 16
    elif base == 'o':
        b = 8
    elif base == 'b':
        b = 2
    else:
        raise ValueError
    count = 1
    v = v / b
    while v > 0:
        count += 1
        v = v / b
    return count

def time_formatter(secs):
    '''将由 1970-01-01 00:00:00 起的秒数转换为时间。'''
    origin = datetime.datetime(1970, 1, 1)
    return origin + datetime.timedelta(seconds=secs)

def unpack_int(s):
    size = len(s)
    if size == 2:
        v, = struct.unpack_from('>H', s)
    elif size == 4:
        v, = struct.unpack_from('>L', s)
    elif size == 1:
        v, = struct.unpack_from('>B', s)
    elif size == 3:
        v, = struct.unpack_from('>L', '\x00' + s)
    elif size == 8:
        v, = struct.unpack_from('>Q', s)
    else:
        raise UtilsError('Invalid length of int to unpack: ' + str(size))
    return v

def pack_int(v, size):
    if size == 2:
        s = struct.pack('>H', v)
    elif size == 4:
        s = struct.pack('>L', v)
    elif size == 1:
        s = struct.pack('>B', v)
    elif size == 3:
        s = struct.pack('>L', v)[1:]
    elif size == 8:
        s = struct.pack('>Q', v)
    else:
        raise UtilsError('Invalid length of int to pack: ' + str(size))
    return s

def identifier_asin(epub_file):
    try:
        z = zipfile.ZipFile(epub_file, 'r')
        content = z.open('OEBPS/content.opf').read()
        soup = BeautifulSoup(content)
        he_asin = soup.find('dc:identifier', attrs={'opf:scheme' : 'ASIN'})
        if he_asin is None:
            print 'Info: ASIN not found in the metadata of the epub file.'
            return None
        else:
            asin = he_asin.string
            #asin = 'B00aaaaaaa'
            if not re.match('B00[0-9A-Z]{7}', asin):
                print 'Warning: "' + asin + '"', 'seems not like a valid ASIN.'
            return str(unicode(asin))
    except KeyError:
        print 'Warning: ASIN not identified. Cannot access OEBPS/content.opf in the epub file.'
        return None

def get_epub_title(epub_file):
    try:
        z = zipfile.ZipFile(epub_file, 'r')
        content = z.open('OEBPS/content.opf').read()
        soup = BeautifulSoup(content)
        he_title = soup.find('dc:title')
        if he_title is None:
            return None
        return unicode(he_title.string)
    except KeyError:
        return None
