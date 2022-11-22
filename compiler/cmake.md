# CMake 基础

## 语法

### PROJECT

指定工程名字和支持的语言

`PROJECT (HELLO)` 指定了工程的名字，并且支持所有语言

`PROJECT (HELLO CXX)` 指定工程名，支持 C++

`PROJECT (HELLO C CXX)` 支持 C 和 CXX

该指定隐式定义了两个 CMAKE 的变量

`<projectname>_BINARY_DIR`，本例中是 `HELLO_BINARY_DIR`

`<projectname>_SOURCE_DIR`，本例中是 `HELLO_SOURCE_DIR`

MESSAGE 关键字就可以直接使用这两个变量

如果改了工程名，上述两个变量名就会改变，因此又定义了两个预定义变量：`PROJECT_BINATY_DIR` 和 `PROJECT_SOURCE_DIR`，这两个变量和 `HELLO_BINARY_DIR`，`HELLO_SOURCE_DIR` 是一致的

### SET

用来显示指定变量

`SET(SRC_LIST main.cpp)` SRC_LIST 变量就包含了 main.cpp

也可以 `SET(SRC_LIST main.cpp t1.cpp t2.cpp)`

### MESSAGE

向终端输出用户自定义的信息

主要包括三种信息：

* `SEND_ERROR`，产生错误，生成过程被跳过
* `SATUS`，输出前缀为 `--` 的信息
* `FATAL_ERROR`，立即终止所有 cmake 过程

### ADD_EXECUTABLE

生成可执行文件

`ADD_EXECUTABLE(hello $(SRC_LIST)`
