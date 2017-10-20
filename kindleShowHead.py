# encoding: utf-8
import sys
import os.path
import getopt
import Tkinter

from kindleunpack.utf8_utils import utf8_argv, add_cp65001_codec, set_utf8_default_encoding, utf8_str
from kindleunpack.mobi_sectioner import Sectionizer, describe
from kindleunpack.mobi_header import MobiHeader, dump_contexth

def getEpubHead():
    pass

def guiShow(headers, filePath):
    top = Tkinter.Tk()
    top.title(filePath)

    text = Tkinter.Text(height=25, width=80, font='SimSun')
    text.insert(Tkinter.INSERT, '\n'.join(headers))
    text.pack(expand=Tkinter.YES, fill=Tkinter.BOTH)  # 将按钮pack，充满整个窗体(只有pack的组件实例才能显示)

    # cnames = StringVar()
    # cnames.set(tuple(headers))
    # Listbox(top, listvariable=cnames, width=100).grid()

    top.mainloop()

def showBookInfo(infile):
    ext = os.path.splitext(infile)[1]

    if ext in ['.epub']:
        headers = getEpubHead(infile)
    else:
        sect = Sectionizer(infile)
        if sect.ident != 'BOOKMOBI' and sect.ident != 'TEXtREAd':
            raise 'Invalid file format'
        mh = MobiHeader(sect,0)
        headers = mh.get_exth(ext[1:])

    guiShow(headers, infile)

def usage(progname):
    print("")
    print("Description:")
    print("   Simple Program to show Mobi/azw3 Meta Info.")
    print("  ")
    print("Usage:")
    print("  %s infile.mobi" % progname)
    print("  ")
    print("Options:")
    print("    -h           print this help message")

def main(argv=utf8_argv()):
    print("Mobi Show Meta 1.0")
    progname = os.path.basename(argv[0])
    try:
        opts, args = getopt.getopt(argv[1:], "h")
    except getopt.GetoptError, err:
        print str(err)
        usage(progname)
        sys.exit(2)

    if len(args) != 1:
        usage(progname)
        sys.exit(2)

    for o, a in opts:
        if o == "-h":
            usage(progname)
            sys.exit(0)

    infile = args[0]
    showBookInfo(infile)

if __name__ == '__main__':
    add_cp65001_codec()
    set_utf8_default_encoding()
    sys.exit(main())