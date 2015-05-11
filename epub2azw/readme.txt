epub2azw 是一个用于修改亚马逊 mobi/azw 格式电子书，以及查看其文件结构
信息的 Python 脚本包。

1. 运行环境

使用 epub2azw 包之前，需要安装下列软件：

(1) Python 2.7.x；
    下载网址： http://www.python.org/

(2) Python 图像处理模块 Pillow；
    用于生成封面缩略图。

    安装方式：在命令行下执行
        easy_install Pillow
    联网下载、安装 Pillow。（easy_install 是 Python 2.7 自带的工具，在
    scripts 目录下）

(3) Python 处理 HTML/XML 文件 的模块 Beautiful Soup；
    用于解析 epub 文件里的 "OEBPS/content.opf" 以获取 ASIN。

    安装方式：在命令行下执行
        easy_install BeautifulSoup4
    联网下载、安装 Beautiful Soup。

(4) KindleGen。
    用于将 epub 格式文件转换为亚马逊 mobi 格式文件。注意将 KindleGen
    的安装路径加入系统的环境变量 PATH 里，保证在命令行下能够直接运行
    kindlegen.exe 命令。

说明： epub2azw 仅在 Win7 + ActivePython 环境下测试过，在 linux、mac
下会碰到文件名编码的问题。

2. 安装与使用

epub2azw 的使用方式有两种：
(1) 在命令行下调用；
(2) 作为 Sigil 的插件使用。
下面分别说明。

(1) 在命令行下调用：

  a. 解压缩 epub2azw_v0.3.x.zip；

  b. 将安装目录加入系统的环境变量 PATH 里；

  c. 在命令行下进入 epub 文件所在的目录，运行命令
    	 python epub2azw.py
     可将当前目录下所有的 epub 格式电子书转换为 azw3 格式。

  d. 在 epub 文件所在的目录下，运行命令
         python dump.py <book>
     可将指定 mobi/azw3 格式电子书的文件结构保存到 .log 日志文件里。其
     中 <book> 为 mobi/azw3 文件名。例如
	 python dump.py foo.azw3
     输出日志文件 foo-dump.log。

(2) 作为 Sigil 的插件使用：

  a. 在 Sigil 0.8.x 里点击菜单“Plugins->Manage Plugins”打开插件管理
     对话框；

  b. 点击“Add Plugin”，选择文件 epub2azw_v0.3.x.zip，完成安装；

  c. 在 Sigil 0.8.x 里打开 epub 文件，完成文件编辑；

  d. 点击菜单“Plugins->Output->epub2azw”调用 epub2azw 脚本。

3. 说明

    a) 为了成功地进行格式转换，请尽量保证 epub 文件的规范性。在运行
       epub2azw.py 时，会首先输出 kindlegen 的信息，当其中没有警告时，
       后续转换一般都能成功完成。

    b) 生成的 azw3 文件通过 USB 连线直接复制到 Kindle 上，会被当作官方
       电子书，而不是个人文档。

    c) 生成的 azw3 文件自带大尺寸 (220*330) 的封面缩略图。如果在 epub
       文件里的 content.opf 里将该书的亚马逊 ASIN 代码设置为元数据，形
       如：
           <dc:identifier opf:scheme="ASIN">B00I2KODJ4</dc:identifier>
       则将在 Kindle 通过 wifi 联网时从亚马逊官网获取封面缩略图。
