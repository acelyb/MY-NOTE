# ELF 基础

## 目标文件

编译器编译源代码后生成的文件叫做目标文件，文件类型为 **ELF(Executable and Linkable Format)**

目标文件只是ELF文件的**可重定位文件(Relocatable file)**，ELF文件一共有4种类型：Relocatable file、Executable file、Shared object file 和 Core Dump file

ELF 文件存放数据的格式也是固定的，计算机在解析目标文件时，就是按照它每个字段的数据结构进行逐字解析的。ELF 文件结构信息定义在 /usr/include/elf.h 中，整个 ELF 文件的结构如下图：

| ELF Header |
| :--: |
| .text |
| .data |
| .bss |
| ...(other sections) |
| Section header table |
| String Tables |
| Symbol Tables |
| ... |

宏观上看，可分为四个部分

| ELF header (ELF 头部) |
| :--: |
| Program header table (程序头表) |
| Sections (节) |
| Section header table (节头表) |

在 Linux 系统中，一个 ELF 文件主要用来表示3种类型的文件：

1. 可执行文件：被操作系统中的加载器从硬盘上读取，载入到内存中去执行
2. 目标文件：被链接器读取，用来产生一个可执行文件或者共享库文件
3. 共享库文件：在动态链接的时候，由 ld-linux.so 来读取

链接器看 ELF，看不见 Program header table

加载器看 ELF，看不见 Section header table，并将 Section 改为 Segment

可以理解为：一个 Segment 可能包含一个或者多个 Sections

| | ELF header (ELF 头部) | |
|:--: | :--: | :--: |
| 加载器看到的是1个segment | Program header table (程序头表) | |
| Segment | .text | Section 1 |
| Segment | .rodata | Section 2 |
| | .data | |
| | .bss | |
| | Section header table (节头表) | 链接器看到的是2个 Sections |

### ELF Header

ELF Header 是 ELF 文件的第一部分，64 bit 的 ELF 文件头的结构体如下：

```cpp
typedef struct
{
  unsigned char e_ident[EI_NIDENT]; /* Magic number and other info */
  Elf64_Half    e_type;         /* Object file type */
  Elf64_Half    e_machine;      /* Architecture */
  Elf64_Word    e_version;      /* Object file version */
  Elf64_Addr    e_entry;        /* Entry point virtual address */
  Elf64_Off e_phoff;        /* Program header table file offset */
  Elf64_Off e_shoff;        /* Section header table file offset */
  Elf64_Word    e_flags;        /* Processor-specific flags */
  Elf64_Half    e_ehsize;       /* ELF header size in bytes */
  Elf64_Half    e_phentsize;        /* Program header table entry size */
  Elf64_Half    e_phnum;        /* Program header table entry count */
  Elf64_Half    e_shentsize;        /* Section header table entry size */
  Elf64_Half    e_shnum;        /* Section header table entry count */
  Elf64_Half    e_shstrndx;     /* Section header string table index */
} Elf64_Ehdr;
```

Header 中主要存放的是一些基本信息，通过 Header 中的信息，我们可以确定后面其他字段的大小和起始地址，通常比较关心的部分是：ELF 文件类型、是 32bit 还是 64bit、Header 部分大小、Section 部分大小和拥有 Section 的个数等

### Section

Section 对应结构体如下：

```cpp
typedef struct
{
  Elf64_Word  sh_name;    /* Section name (string tbl index) */
  Elf64_Word  sh_type;    /* Section type */
  Elf64_Xword sh_flags;   /* Section flags */
  Elf64_Addr  sh_addr;    /* Section virtual addr at execution */
  Elf64_Off sh_offset;    /* Section file offset */
  Elf64_Xword sh_size;    /* Section size in bytes */
  Elf64_Word  sh_link;    /* Link to another section */
  Elf64_Word  sh_info;    /* Additional section information */
  Elf64_Xword sh_addralign;   /* Section alignment */
  Elf64_Xword sh_entsize;   /* Entry size if section holds table */
} Elf64_Shdr;
```

Section 部分主要存放的是机器指令代码和数据，通常我们比较的 Section 是 .text（存放代码）、.data（存放全局静态变量和局部静态变量）和 .bss（存未初始化的全局变量和局部静态变量）

### 字符串表项 Entry

在一个 ELF 文件中，存在很多字符串，例如：变量名、Section名称、链接器加入的符号等等，这些字符串的长度都是不固定的，因此用一个固定的结构来表示这些字符串，肯定是不现实的

于是，把这些字符串集中起来，统一放在一起，作为一个独立的 Section 来进行管理

# 参考链接

1. [ELF文件介绍](https://blog.csdn.net/nirendao/article/details/123883856)