# 1. 安装

后续需要看 LaTex 和 markdown 怎么结合

初步看，markdown 可以兼容 LaTex 中的公式。但不确定是否支持 LaTex 的排版方式

# 2. Markdown 基础

## 1. 标题

**使用 = 和 - 标记一级和二级标题**

注意：由于分割线也是“---”，因此在使用分割线时，一定要空一行，不然会把上方的文字识别为二级标题

一级标题
===

二级标题
---

**使用 # 标记**

在行首插入1到6个 # 再加空格，对应到标题1到6级

注意：# 后需要有空格

# 一级标题

## 二级标题

### 三级标题

#### 四级标题

##### 五级标题

###### 六级标题

## 2. 段落

**段落的换行是使用两个以上空格加上回车**

Markdown 段落1  
Markdown 段落2

**也可以再段落后面使用一个空行来表示重新开始一个段落**

Markdown 段落1

Markdown 段落2

## 3. 字体

以下是正文字体各种格式展示

*斜体*

_xieti_

**粗体**

__cuti__

***斜体加粗***

___xietijiacu___

## 4. 分割线

可以在一行中用三个以上的*、-、_来建立一个分割线，行内不能含有其他符号等。
可以在*或是-中间插入空格。下面每种写法都可以建立分割线：

***

* * *

*******

- - -

-------

_ _ _

## 5. 修饰

### 删除线

如果段落上的文字要添加删除线，只需在文字的两端加两个~即可：

~~删除线~~

### 下划线

下划线可以通过 HTML 的 `<u>` 标签来实现：

<u>下划线</u>

### 高亮

==高亮==

### 注脚

注脚1[^id1]

注脚2[^id2]

[^id1]:这是注脚1

[^id2]:这是注脚2

## 6. 列表

Markdown 支持有序表和无序表

### 无序表

无序表使用 * 、+ 、- 、作为标记，这些标记后面需要添加一个空格，之后再填写内容

* 第一项
* 第二项
* 第三项

+ 第一项
+ 第二项
+ 第三项

- 第一项
- 第二项
- 第三项

### 有序表

有序表使用数字并加上 . 来表示

1. 第一项
2. 第二项
3. 第三项
7. 第四项

如果第一项序号不是1

7. 第一项
8. 第二项

### 列表嵌套

列表嵌套只需要在子列表中的选项前添加四个空格即可

1. 第一项
    * 第一项嵌套的第一个元素
    * 第一项嵌套的第二个元素
2. 第二项
   1. 第二项嵌套的第一个元素
   2. 第二项嵌套的第二个元素

## 7. 区块

### 区块

Markdown 区块的引用是在段落开头使用 > 符号，后面紧跟一个空格符号

另外区块是可以嵌套的，一个 > 符号是最外层，两个 >> 符号是第一层嵌套，以此类推

> 区块引用
> Markdown区块

> 最外层
>> 第一层嵌套
>>> 第二层嵌套

### 区块中使用列表

> 区块中使用列表
>
> 1. 第一项
> 2. 第二项

### 列表中使用区块

如果需要在列表项内放进区块，需要在 > 前添加四个空格的缩进

* 第一项
    > 列表中使用区块
    > 列表中使用区块
* 第二项

## 8. 代码

如果是段落上的一个函数或者片段的代码可以用反引号把它包起来

行内代码 `printf()`

代码区块使用4个空格或者一个制表符

    print

也可以用 ``` 包裹一段代码，并指定一种语言（也可以不指定）

```c
include<stdio.h>
int main() {
    printf("Hello World!");
    return 0;
}
```

## 9. 链接

这是一个链接[Google](https://www.google.com)

直接使用链接地址：<https://www.google.com>

高级链接：通过变量来设置一个链接，变量赋值在文档末尾进行

这个链接用 idgoogle 作为网址变量[Google][idgoogle]

这个链接用 idbing 作为网址变量[Bing][idbing]

然后在文档的结尾处为变量赋值

[idgoogle]: https://www.google.com

[idbing]: https://cn.bing.com/

## 10. 图片

图片语法格式如下：

1. 开头一个感叹号
2. 接着一个方括号，里面放上图片的替代文字
3. 接着一个普通括号，里面放上图片的网址，最后还可以用引号包住并加上选择性的 'title' 属性的文字

利用 markdown 在编写文档时插入图片是默认靠左，有些时候将图片设置为居中时可以更加美观，这时就需要在图片的信息前边添加如下语句：

    <div align=center>![Alt pic] (http:...)
    
    如果想将图片位于右侧，只需要将center改为right

设置图片大小

    <img src="http:..." width = "100" height = "100" div align=right />

如上格式，在图片的最后添加 width = "100" height = "100"，就可以设置图片的大小。也可以在后面输入百分比为多少，如 width = 20% height = 20%

图片使用 PicGo + GitHub 作为图床

更多图片使用方法参照网上方法，如 <https://www.zhihu.com/question/23378396>

许多方法并不可用，具体效果有差异

以下为演示

![](https://raw.githubusercontent.com/acelyb/images/main/img/IMG_9745(20210315-125356).JPG)

<img src='https://raw.githubusercontent.com/acelyb/images/main/img/IMG_9745(20210315-125356).JPG#pic_center' width=50%></img>

![](https://raw.githubusercontent.com/acelyb/images/main/img/IMG_9746(20200916-160836).JPG){:width="50%"}

<img src="https://raw.githubusercontent.com/acelyb/images/main/img/IMG_9746(20200916-160836).JPG" width=50% alt="pic_name" align=center />

<div align="center">
![](https://raw.githubusercontent.com/acelyb/images/main/img/IMG_9746(20200916-160836).JPG)
</div>

## 11. 表格

制作表格使用 | 来分隔不同单元格，使用 - 来分割表头和其他行

对齐方式：

1. -: 设置内容和标题栏居右对齐
2. :- 设置内容和标题栏居左对齐
3. :-: 设置内容和标题栏居中对齐

|  表头  |  表头  |
|  ---  |  ---  |
| 单元格 | 单元格 |

| 居左对齐 | 居中对齐 | 居右对齐 |
| :---- | :----: | ----: |
| 单元格 | 单元格 | 单元格 |
| 单元格 | 单元格 | 单元格 |

# 3. Markdown 进阶

## 1. 表情

表情 :smile:

to be continued

## 2. 公式

### 行内公式

行内公式 $\theta = x^2$

### LaTex公式

当你需要在编辑器中插入数学公式时，可以使用两个美元符 $$ 包裹 TeX 或 LaTeX 格式的数学公式来实现。提交后，问答和文章页会根据需要加载 Mathjax 对数学公式进行渲染

$\sum\limits_{i=0}^{n}i^2$

## 3. 文本

### 加入上下标

#### 上标

X^2^

上标<sup>TM</sup>

#### 下标

H~2~O

CO<sub>2</sub>

### 改变字体、大小、颜色

<font face="黑体">我是黑体字</font>

<font face="幼圆">我是幼圆字</font>

<font color=red>我是红色</font>

<font color=yellow>我是黄色</font>

<font color=blue>我是蓝色</font>

<font size=1>我是尺寸</font>

<font face="幼圆" color=green size=1>幼圆 绿色 尺寸为1</font>

<table><tr><td bgcolor=yellow>背景色 黄色 </td></tr></table>

<center>居中</center>

<p align="right">右对齐</p>

## 4. 支持的 HTML 元素

不在 Markdown 涵盖范围内的标签，都可以直接再文档里用 HTML 撰写

目前支持的 HTML 元素有：`<kbd> <b> <i> <em> <sup> <br>` 等

## 5. 转义

Markdown 使用了很多特殊符号来表示特定的意义，如果需要显示特定的符号则需要使用转移字符，Markdown 使用反斜杠转义特殊字符

Markdown 支持以下这些符号前面加上反斜杠来帮助插入普通的符号：

    \   反斜线
    `   反引号
    *   星号
    _   下划线
    {}  花括号
    []  方括号
    ()  小括号
    #   井字号
    +   加号
    -   减号
    .   英文句点
    !   感叹号

## 6. 流程图

to be continued

## 7. 代办事项

- [x] test1
- [ ] test2
- [ ] test3

## 8. 图形

### 1. mermaid

to be continued...

#### 参考文档

1. [官方文档](https://mermaid-js.github.io/mermaid/#/)
2. [中文文档](https://github.com/mingcheng/mermaid-gitbook-zh)

### 2. flow

to be continued...

# 4. LaTex 与 Markdown

to be continued

# 5. 相关链接

[markdown 中使用LaTex公式](https://www.cnblogs.com/bubcs/p/12736151.html)

[vscode 关于 markdown 说明](https://code.visualstudio.com/docs/languages/markdown)

[vscode 配置](https://zhuanlan.zhihu.com/p/139140492)
