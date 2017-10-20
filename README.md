# 我的电子书相关工具合集

运行环境：windows、python2

## 脚本说明

### epub2azw

[原版](http://www.hi-pda.com/forum/viewthread.php?tid=1524119)，未修改

### kindleunpack/kindleunpack

提取 azw3、mobi 的 epub。[原版](http://github.com/kevinhendricks/KindleUnpack)

### kindlestrip

精简 kindlegen 生成的 mobi。根据[原版](http://github.com/jefftriplett/kindlestrip)修正了 kindlestrip 输入路径中存在非 gbk 字符从而无法读取的问题。

注：用 kindlegen 生成 mobi 可添加参数 `-dont_append_source`

### dualmetafix_mmap

给 mobi/azw3 加上 ASIN 和 EBOK，这样手动放入 mobi 没有 "个人文档" 字样，发送到 kindle 可显示封面。

根据 [原版](http://www.mobileread.com/forums/showpost.php?p=2839085&postcount=58) 略有修改。

### kindleFixCoverBySend

功能：补全推送 mobi 缺失的封面（kindlegen生成的 mobi）
使用：双击运行 kindleFixCoverBySend，如果有提示按回车键忽略或输入路径手动补充封面。路径示例："d:\\cover.jpg" 双引号必须。

### kindleCleaner

清理 kindle sdr 文件夹，python3

### kindleShowHead

简单地显示 mobi、azw3 文件的信息。

使用方式： `pythonw kindleShowHead.py "XX路径"`

## 构建 exe

在 32位 python2.7 版本下，运行命令 `py -2 toexe.py`