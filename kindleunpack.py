# encoding: utf-8
import os
import sys
import getopt

from kindleunpack import kindleunpack
from kindleunpack.utf8_utils import utf8_argv, add_cp65001_codec
add_cp65001_codec()
from kindleunpack.kindleunpack import unpackBook

def usage(progname):
    print ""
    print "Description:"
    print "  Unpacks an unencrypted Kindle/MobiPocket ebook to html and images"
    print "  or an unencrypted Kindle/Print Replica ebook to PDF and images"
    print "  into the specified output folder."
    print "Usage:"
    print "  %s -r -s -p apnxfile -d -h --epub_version= infile [outdir]" % progname
    print "Options:"
    print "    -h                 print this help message"
    print "    -i                 use HD Images, if present, to overwrite reduced resolution images"
    print "    -s                 split combination mobis into mobi7 and mobi8 ebooks"
    print "    -p APNXFILE        path to an .apnx file associated with the azw3 input (optional)"
    print "    --epub_version=    specify epub version to unpack to: 2, 3, A (for automatic) or "
    print "                         F (force to fit to epub2 definitions), default is 2"
    print "    -d                 dump headers and other info to output and extra files"
    print "    -r                 write raw data to the output folder"


def main():
    # global DUMP
    # global WRITE_RAW_DATA
    # global SPLIT_COMBO_MOBIS

    print "KindleUnpack v0.77"
    print "   Based on initial mobipocket version Copyright © 2009 Charles M. Hannum <root@ihack.net>"
    print "   Extensive Extensions and Improvements Copyright © 2009-2014 "
    print "       by:  P. Durrant, K. Hendricks, S. Siebert, fandrieu, DiapDealer, nickredding, tkeo."
    print "   This program is free software: you can redistribute it and/or modify"
    print "   it under the terms of the GNU General Public License as published by"
    print "   the Free Software Foundation, version 3."

    argv = utf8_argv()
    progname = os.path.basename(argv[0])
    try:
        opts, args = getopt.getopt(argv[1:], "dhirsp:", ['epub_version='])
    except getopt.GetoptError, err:
        print str(err)
        usage(progname)
        sys.exit(2)

    if len(args)<1:
        usage(progname)
        sys.exit(2)

    apnxfile = None
    epubver = '2'
    use_hd = False

    for o, a in opts:
        if o == "-h":
            usage(progname)
            sys.exit(0)
        if o == "-i":
            use_hd = True
        if o == "-d":
            kindleunpack.DUMP = True
        if o == "-r":
            kindleunpack.WRITE_RAW_DATA = True
        if o == "-s":
            kindleunpack.SPLIT_COMBO_MOBIS = True
        if o == "-p":
            apnxfile = a
        if o == "--epub_version":
            epubver = a

    if len(args) > 1:
        infile, outdir = args
    else:
        infile = args[0]
        outdir = os.path.splitext(infile)[0]

    infileext = os.path.splitext(infile)[1].upper()
    if infileext not in ['.MOBI', '.PRC', '.AZW', '.AZW3', '.AZW4']:
        print "Error: first parameter must be a Kindle/Mobipocket ebook or a Kindle/Print Replica ebook."
        return 1

    try:
        print 'Unpacking Book...'
        unpackBook(infile, outdir, apnxfile, epubver, use_hd)
        print 'Completed'

    except ValueError, e:
        print "Error: %s" % e
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
