# 内存检查

## valgrind

### 内存泄露 —— memcheck

```bash
# abc 为待测试的指令
valgrind --leak-check=full --show-reachable=yes --tool=memcheck --log-file=log.txt abc
```

### 内存开销 —— massif

```bash
valgrind --tool=massif --time-unit=B abc
# 可视化内存信息
massif-visualizer massif.out.xxx
```

## AddressSanitizer

检查内存泄露 / 越界

### gcc 命令行参数

AddressSanitizer 已集成在 `gcc` 中

可在使用 `gcc` 时直接添加命令行参数

```bash
# 用 -fsanitize=address 选项编译和链接你的程序
# 用 -fno-omit-frame-pointer 编译，以在错误消息中添加更好的堆栈跟踪
# 增加 -O1 以获得更好的性能
gcc -sanitize=address -fno-omit-frame-pointer -O1 -g abc.cpp -o abc
```

### 修改 cmake 过程

修改 CMakeLists.txt，添加 `-sanitize=address -fno-omit-frame-pointer -O1` 参数

```bash
set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=address -fno-omit-frame-pointer")
set (CMAKE_LINKER_FLAGS_DEBUG "${CMAKE_LINKER_FLAGS_DEBUG} -fsanitize=address -fno-omit-frame-pointer")
```

编译后直接运行测试代码可能会报错

```bash
==10987==ASan runtime does not come first in initial library list; you should either link runtime to your application or manually preload it with LD_PRELOAD.
```

原因是未添加动态库，需要添加动态库链接

```bash
# libasan.so 的位置可能有变
export LD_PRELOAD=/usr/lib/gcc/x86_64-linux-gnu/5/libasan.so
# 执行测试脚本
python test.py
# 执行可执行程序
./test
# 取消路径设置
unset LD_PRELOAD

# 直接执行
LD_PRELOAD=/usr/lib/gcc/x86_64-linux-gnu/5/libasan.so ./test
```
