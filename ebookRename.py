# encoding=utf-8
import sys
import os.path
import getopt

from kindleunpack.utf8_utils import utf8_argv, add_cp65001_codec, set_utf8_default_encoding, utf8_str
from kindleunpack.mobi_sectioner import Sectionizer, describe
from kindleunpack.mobi_header import MobiHeader, dump_contexth

def getMobiFileName(infile):
    """ 存在问题， """
    sect = Sectionizer(infile)
    if sect.ident != 'BOOKMOBI' and sect.ident != 'TEXtREAd':
        raise 'Invalid file format'
    mh = MobiHeader(sect,0)

    # Error: Updated_Title 可能不存在，但 calibre 能得到标题
    titles = mh.metadata.get('Updated_Title')
    if not titles:
        print('无法得到标题')
        return

    title = titles[0]

    title = title.decode(mh.codec)
    print('New Title: %s' % title)
    author = '、'.join([au.decode(mh.codec) for au in mh.metadata['Creator']])

    return '%s - %s' % (title, author)

def renameOneBook(infile):
    ext = os.path.splitext(infile)[1]

    newName = None
    if ext in ['.epub']:
        pass
    elif ext in ['.azw3', '.azw4', '.azw', '.mobi']:
        newName = getMobiFileName(infile)

    if newName:
        os.rename(infile, newName + ext)

def main(argv=utf8_argv()):
    if len(argv) == 1:
        sys.exit(2)
    else:
        for path in argv[1:]:
            renameOneBook(path)

if __name__ == '__main__':
    add_cp65001_codec()
    set_utf8_default_encoding()
    sys.exit(main())
