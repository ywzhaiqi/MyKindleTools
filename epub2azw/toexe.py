# encoding: utf-8
from distutils.core import setup
import py2exe
import sys
 
# this allows to run it with a simple double click.
sys.argv.append('py2exe')

# 64 位不支持 bundle_files
py2exe_options = {
        "compressed": 1,
        "optimize": 2,
        "ascii": 0,
        "bundle_files": 1,
        #"build_base": "",
        #"dist_dir": "bin",
        "dll_excludes": ["w9xpopen.exe"]
        }
setup(
    console = [{"script": "epub2azw.py", "icon_resources": [(1, "azw3.ico")] }],
    zipfile = None,
    options = {"py2exe": py2exe_options}
    )