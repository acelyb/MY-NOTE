> 2022-06-07
> 1. composeXram 能否合并？现 Xram 都想获取字节地址，第一个参数目的是判断 Xram
> 2. omposeConstAddr 存在风险，ddr 是 32bit，而 ofst 可能超过 32bit，而目前函数实现是直接相加
> 3. 重写代码时注意加 **override**

> 2022-06-08
> 1. C 语言结构体指针（[参考链接](http://c.biancheng.net/view/2033.html)）

> 2022-06-13
> 1. `c_interface.cpp`是对外暴露的接口，需要考虑到兼容性