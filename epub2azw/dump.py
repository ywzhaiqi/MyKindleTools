#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import KindleEBook

mobi_file = sys.argv[1]
KindleEBook.dump_file(mobi_file.decode('mbcs'))
#extract_kf8(mobi_file.decode('mbcs'))
