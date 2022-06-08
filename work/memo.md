> 2022-06-07
>
> 1. composeXram 能否合并？现 Xram 都想获取字节地址，第一个参数目的是判断 Xram
> 2. omposeConstAddr 存在风险，ddr 是 32bit，而 ofst 可能超过 32bit，而目前函数实现是直接相加
> 3. 重写代码时注意加 **override**