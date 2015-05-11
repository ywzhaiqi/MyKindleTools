#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Tkinter import *
import ttk
import os
import inspect
import codecs
import ConfigParser

class epub2azw_opt:
    '''epub2azw 选项
    '''
    note = u'在运行时不显示本窗口的情况下，可以在配置文件 "C:\\Users\\<username>\\AppData\\Local\\sigil-ebook\\sigil\\plugins\\epub2azw\\epub2azw.ini" 里通过修改设置\n' + 'popup = 1\n' + u'重新显示本窗口。'

    def __init__(self):
        #
        self.tk = Tk()
        self.tk.title(u'epub2azw 选项')
        self.sv_compress = StringVar()
        self.sv_compress.set('-c1')
        self.sv_verbose = StringVar()
        self.sv_gif = StringVar()
        self.sv_thumbnail = StringVar()
        self.sv_thumbnail.set('none')
        self.sv_popup = IntVar()
        self.sv_popup.set(1)
        # 导入配置文件
        self.import_config()
        ##############################
        #
        # 窗口布局
        #
        ##############################
        pw = ttk.Panedwindow(self.tk, orient=VERTICAL)
        pw.grid(row=0, column=0, padx=10, pady=10)
        # kindlegen 命令选项
        lf_kindlegen = ttk.Labelframe(pw, text=u'KindleGen 命令选项')
        pw.add(lf_kindlegen)
        ttk.Radiobutton(lf_kindlegen, text=u'-c0：不压缩',
                        variable=self.sv_compress, value='-c0').grid(row=0, column=0, padx=5, sticky=W)
        ttk.Radiobutton(lf_kindlegen, text=u'-c1：标准 DOC 压缩',
                        variable=self.sv_compress, value='-c1').grid(row=1, column=0, padx=5, sticky=W)
        ttk.Radiobutton(lf_kindlegen, text=u'-c2：Kindle huffdic 压缩',
                        variable=self.sv_compress, value='-c2').grid(row=2, column=0, padx=5, sticky=W)
        ttk.Separator(lf_kindlegen, orient=HORIZONTAL).grid(row=3, column=0, sticky='WE', padx=5, pady=10)
        ttk.Checkbutton(lf_kindlegen, text=u'-verbose： 在电子书转换过程中提供更多信息', 
                        variable=self.sv_verbose, onvalue='-verbose', offvalue='').grid(row=4, column=0, padx=5, sticky=W)
        ttk.Checkbutton(lf_kindlegen, text=u'-gif：转换为 GIF 格式的图像（书中没有 JPEG）', 
                        variable=self.sv_gif, onvalue='-gif', offvalue='').grid(row=5, column=0, padx=5, sticky=W)
        # 封面缩略图输出选项
        lf_thumbnail = ttk.Labelframe(pw, text=u'封面缩略图输出选项')
        pw.add(lf_thumbnail)
        ttk.Radiobutton(lf_thumbnail, text=u'不输出封面缩略图',
                        variable=self.sv_thumbnail, value='none').grid(row=0, column=0, padx=5, sticky=W)
        ttk.Radiobutton(lf_thumbnail, text=u'输出 KPW 尺寸的封面缩略图',
                        variable=self.sv_thumbnail, value='kpw').grid(row=1, column=0, padx=5, sticky=W)
        ttk.Radiobutton(lf_thumbnail, text=u'输出 KV 尺寸的封面缩略图',
                        variable=self.sv_thumbnail, value='kv').grid(row=2, column=0, padx=5, sticky=W)
        # 弹出窗口选项
        ttk.Checkbutton(self.tk, text=u'下次运行时显示本窗口',
                        variable=self.sv_popup, onvalue=1, offvalue=0).grid(row=3, column=0,
                                                                            padx=10, sticky=W)
        Label(self.tk, text=epub2azw_opt.note,
              wraplength=320, justify=LEFT).grid(row=4, column=0,
                                                 padx=10, sticky=W)
        Button(self.tk, text=u'确定', width=10, 
               command=self.command_ok_clicked).grid(row=5, column=0, padx=10, pady=10, sticky=E)

    def set(self):
        '''设置 epub2azw 选项
        '''
        self.tk.mainloop()

    def command_ok_clicked(self):
        self.export_config()
        self.tk.destroy()

    def kindlegen(self):
        '''KindleGen 命令行参数。
        '''
        return ' '.join([self.sv_compress.get(),
                         self.sv_verbose.get(),
                         self.sv_gif.get()]).rstrip(' ')

    def thumbnail(self):
        return self.sv_thumbnail.get()

    def get_module_home_path(self):
        fn = inspect.getfile(inspect.currentframe())
        return os.path.dirname(fn)

    def import_config(self):
        '''导入配置文件。
        '''
        home_path = self.get_module_home_path()
        config_path = os.path.join(home_path, 'epub2azw.ini')
        if os.path.isfile(config_path):
            config = ConfigParser.RawConfigParser()
            config.readfp(codecs.open(config_path, encoding='utf-8'))
            #
            self.sv_popup.set(config.getint('general', 'popup'))
            #
            self.sv_compress.set(config.get('kindlegen', 'compress'))
            self.sv_verbose.set(config.get('kindlegen', 'verbose'))
            self.sv_gif.set(config.get('kindlegen', 'gif'))
            #
            self.sv_thumbnail.set(config.get('thumbnail', 'output'))

    def export_config(self):
        '''导出配置文件。
        '''
        config = ConfigParser.RawConfigParser()
        config.add_section('general')
        config.set('general', 'popup', self.sv_popup.get())
        #
        config.add_section('kindlegen')
        config.set('kindlegen', 'compress', self.sv_compress.get())
        config.set('kindlegen', 'verbose', self.sv_verbose.get())
        config.set('kindlegen', 'gif', self.sv_gif.get())
        #
        config.add_section('thumbnail')
        config.set('thumbnail', 'output', self.sv_thumbnail.get())
        #
        home_path = self.get_module_home_path()
        config_path = os.path.join(home_path, 'epub2azw.ini')
        with open(config_path, 'wb') as configfile:
            config.write(configfile)
