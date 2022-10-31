# Basic design

1. 从输入文件拷贝实际数据到输出文件
2. 将数据从输入文件复制到输出文件是受 I/O 限制的，因此在将数据从一个文件复制到另一个文件时应该有空间来执行计算密集型任务
3. 在输入文件准备好前允许链接器预加载文件并分析，需要将链接器分为两步
4. 通过字符串驻留技术处理 symbol
5. 可合并字符串
6. 忽略静态文档符号表，直接读取静态文档成员
7. 并行扫描 .got

# 参考链接

1. [Design and implementation of mold](https://github.com/rui314/mold/blob/main/docs/design.md)
