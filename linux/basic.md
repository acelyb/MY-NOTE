# 软件安装

## 字体安装

### 查看当前系统字体

使用 `fc-list` 命令进行查看

如果没有该命令，需要安装相关软件包

```bash
# ubuntu
sudo apt-get -y install fontconfig xfonts-utils

# centos
yum install -y fontconfig mkfontscale
```

使用 `fc-list` 命令即可显示安装的字体目录

查看安装的中文字体

```bash
fc-list :lang=zh
```

### 安装字体

将字体拷入相应的目录，构建字体索引信息，更新字体缓存

```bash
cp xxx.ttf /usr/share/fonts/
cd /usr/share/fonts/
mkfontscale
mkfontdir
fc-cache
# fc-cache -fv
```

### 常见字体对应的英文

```bash
宋体 SimSun
黑体 SimHei
微软雅黑 Microsoft YaHei
微软正黑体 Microsoft JhengHei
新宋体 NSimSun
新细明体 PMingLiU
细明体 MingLiU
标楷体 DFKai-SB
仿宋 FangSong
楷体 KaiTi
仿宋_GB2312 FangSong_GB2312
楷体_GB2312 KaiTi_GB2312
```
