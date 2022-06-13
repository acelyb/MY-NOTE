# 多文件链接

## CUDA TOOLKIT

### Separate Compilation

device 相关的编译将分为两部：

1. 将 relocatable device code 编译到对应 host object 中，比如 x.o 和 y.o
2. 使用 nvlink 将 x.o 和 y.o 中的 device code 链接到一起得到 a_dlink.o

之所以称第一步编译的 device code 为 relocatable，意思是说这些 device code 在 host object 的位置会在第二步重定位

对比 Whole Program Compilation，我们称其 device code 为 executable device code，意思是编译后的 device code 在 host object 中已经定位好了，一直到生成可执行文件都是不需要重新定位的

### Virtual and Real Architectures

```bash
nvcc x.cu --gpu-architecture=compute_50 --gpu-code=sm_50
```

compute_xx 就是对应 GPU 的 Virtual Architecture，而 sm_xx 就是对应 GPU 的 Real Architecture。至于后面的数字，代表的是 GPU 不同架构的版本

这里的 Virtual 和 Real 架构其实也是两种不同的指令集，其中 Virtual Architecture 会生成一种中间产物 PTX(Parallel Thread Execution)，可以认为它是 Virtual Architecture 的汇编产物。Virtual Architecture 是一个通用的指令集，主要是为了考虑不同显卡之间的兼容性。Real Architecture 提供的是真实 GPU 上的指令集，也是最终 CUDA 程序运行的指令集。所以一般在选择编译选项的时候，Virtual Architecture 的版本要选择低一些，因为这样可以大大提高兼容性，也就是说可以跑在更多的 CUDA 机器上。而 Real Architecture 尽量使用最新的版本，因为一般来说最新的版本会进行更多的优化

CUDA 程序编译时，首先会根据你指定的 Virtual Architecture 选项生成 .ptx 文件，然后再根据 Real Architecture 的选项将 .ptx 文件编译成 .cubin 文件，最终再经过一系列处理 .cubin 文件会链接到目标产物中

### Just-in-Time Compilation

CUDA 中的 JIT 就是在 CUDA 程序运行时，将 .ptx 文件根据目标平台编译为对应的 .cubin 文件，并链接到目标产物中

### 参考文献

1. [NVCC 官方文档](https://docs.nvidia.com/cuda/cuda-compiler-driver-nvcc/index.html#examples)（第六章）
2. [CUDA Binary 官方文档](https://docs.nvidia.com/cuda/cuda-binary-utilities/index.html)
3. [博客1](https://polobymulberry.github.io/2019/03/04/CUDA%E5%AD%A6%E4%B9%A0%E7%B3%BB%E5%88%97(1)%20%7C%20%E7%BC%96%E8%AF%91%E9%93%BE%E6%8E%A5%E7%AF%87/)
4. [博客2](https://blog.csdn.net/jinking01/article/details/105388149)
5. [博客3](https://tech.meituan.com/2015/01/22/linker.html)
