> 2022-06-07
> 1. composeXram 能否合并？现 Xram 都想获取字节地址，第一个参数目的是判断 Xram
> 2. omposeConstAddr 存在风险，ddr 是 32bit，而 ofst 可能超过 32bit，而目前函数实现是直接相加
> 3. 重写代码时注意加 **override**

> 2022-06-08
> 1. C 语言结构体指针（[参考链接](http://c.biancheng.net/view/2033.html)）

> 2022-06-13
> 1. `c_interface.cpp`是对外暴露的接口，需要考虑到兼容性

> 2022-06-14
> 1. extern 属性支持
>> * 2XIR 中全局变量 addvar 操作中根据 VAR_EXTERN 添加 var 的属性，需要根据是否有初始化等属性去判断
>> * xoc/var.h union 中加入 extern 相关属性
>> * elf 处理时 判断 var属性 putglobaldata 中 continue

> 2022-06-16
> 1. bug 解决提测前要自己测一遍，如果经手多的情况需要注意是否所有 patch 都已合入

> 2022-06-19
> 1. loadKernelConfig

> 2022-06-23
> 1. 注意内存对齐
> 2. 减少值传递
> 3. 注意内存管理
> 4. 不做修改的参数要做常量引用
> 5. 申请完内存需要对内存进行拷贝
> 6. 测试时注意检查内存（valgrind / valgrind --show-leak-kinds=yes --log-file=v.log ./kernel_param）

> 2022-06-23
> 1. 核实后再提测
> 2. 本地需要测试自己加的测例
