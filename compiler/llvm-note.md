# LLD

LLD 是 llvm 的链接器。下述笔记以 ELF 二进制类型为例。

## 链接时调用关系

调用关系

```mermaid
graph TD
    lldMain[lldMain] --> elflink[[elf::link]]
    elflink -.-> LinkerDriverlinkerMain[[LinkerDriver::linkerMain]]
    LinkerDriverlinkerMain -.-> LinkerDriverlink[[LinkerDriver::link]]
    LinkerDriverlink -.-> elfparseFile[[elf::parseFile]]
    elfparseFile -.-> dopostparse[[do post parse work]]
    dopostparse -.-> reportDuplicate

    subgraph elf::link
        elflink --> ctx[CommonLinkerContext]
        ctx --> SymbolTable[[SymbolTable::SymbolTable]]
        SymbolTable --> getFilenameWithoutExe[[args::getFilenameWithoutExe]]
        getFilenameWithoutExe --> LinkerDriverlinkerMain
    end

    subgraph LinkerDriver::linkerMain
        LinkerDriverlinkerMain --> parser
        parser --> readConfigs
        readConfigs --> initLLVM
        initLLVM --> createFiles
        createFiles --> inferMachineType
        inferMachineType --> checkOptions
        checkOptions --> LinkerDriverlink
    end

    subgraph LinkerDriver::link
        LinkerDriverlink --> tryCreateFile
        tryCreateFile --> trace-symbol
        trace-symbol --> handleundefined[handle undefined symbol]
        handleundefined --> elfparseFile
        elfparseFile --> hasDynSymTab[deal dynamic symbol table]
        hasDynSymTab --> deallazysymbol[deal symbols defined lazily]
        deallazysymbol --> handleLibcall[handle libcall symbols]
        handleLibcall --> dopostparse
        dopostparse --> declareSymbols[declare linker script's symbols]
        declareSymbols --> excludeLibs
        excludeLibs --> addReservedSymbols
        addReservedSymbols --> scanVersionScript[Apply version scripts]
        scanVersionScript --> compileBitcodeFiles[[LTO]]
        compileBitcodeFiles --> processArmCmseSymbols
        processArmCmseSymbols --> redirectSymbols
        redirectSymbols --> replaceCommonSymbols[[replaceCommonSymbols]]
        replaceCommonSymbols --> aggregatesections[Aggregate sections]
        aggregatesections --> stripsections[Strip sections]
        stripsections --> writeDependencyFile
        writeDependencyFile --> assignsections[Assign sections]
        assignsections --> mergeinputsections[Merge/finalize input sections]
    end

    subgraph elf::parseFile
        elfparseFile --> doParseFile
        doParseFile --> parse[[parse]]
    end

    subgraph parse
        parse --> Handledependentlibraries[Handle dependent libraries]
        Handledependentlibraries --> addDependentLibrary
        addDependentLibrary --> initializeSymbols[[initializeSymbols]]
    end

    subgraph post parse work
        dopostparse --> initSectionsAndLocalSyms[[initSectionsAndLocalSyms]]
        initSectionsAndLocalSyms --> postParse[[postParse]]
    end

    subgraph init Sections And Local Syms
        initSectionsAndLocalSyms --> initializeSections[[initializeSections]]
        initializeSections --> initializeLocalSyms[initialize local symbols]
    end

    subgraph LTO
        compileBitcodeFiles --> compilebitcode[Compile bitcode files and replace bitcode symbols]
    end
```

类图

```mermaid
classDiagram
    CommonLinkerContext ..> LinkerDriver
    CommonLinkerContext ..> SymbolTable

    Symbol --o SymbolTable
    Symbol --o InputFile

    Defined --|> Symbol
    Undefined --|> Symbol
    CommonSymbol --|> Symbol
    SharedSymbol --|> Symbol
    LazyObject --|> Symbol

    ELFFileBase --|> InputFile
    BitcodeFile --|> InputFile
    BinaryFile --|> InputFile
    ObjFile --|> ELFFileBase
    SharedFile --|> ELFFileBase

    class CommonLinkerContext {

    }

    class LinkerDriver {
        -std::unique_ptr~BitcodeCompiler~ lto
        -std::vector~InputFile *~ files
        +SmallVector~std::pair~StringRef, unsigned~, 0~ archiveFiles
        +linkerMain() void
        -createFiles() void
        -link() void
    }

    class SymbolTable {
        -SmallVector~Symbol *, 0~ symVector
        +insert() Symbol *
    }

    class Symbol {
        +InputFile *file
        +resolve(const Undefined &other) void
        +resolve(const CommonSymbol &other) void
        +resolve(const Defined &other) void
        +resolve(const LazyObject &other) void
        +resolve(const SharedSymbol &other) void
        +overwrite(Symbol &sym, Kind k) void
    }

    class Defined {
        +overwrite(Symbol &sym) void
    }

    class Undefined {
        +overwrite(Symbol &sym) void
    }

    class CommonSymbol {
        +overwrite(Symbol &sym) void
    }

    class SharedSymbol {
        +overwrite(Symbol &sym) void
    }

    class LazyObject {
        +overwrite(Symbol &sym) void
    }

    class InputFile {
        #std::unique_ptr~Symbol *[]~ symbols
        #uint32_t numSymbols
        #SmallVector~InputSectionBase *, 0~ sections
    }

    class ELFFileBase {
        #const void *elfSyms
    }

    class BitcodeFile {

    }

    class BinaryFile {

    }

    class ObjFile {
        -ArrayRef~Elf_Word~ shndxTable
        +initSectionsAndLocalSyms() void
        -initializeSections() void
    }

    class SharedFile {

    }

    class Ctx {
        +LinkerDriver driver
    }
```

### elf::link

完成初始化

#### 构建符号表 symtab

`symtab = SymbolTable();`

`symtab` 为全局符号表

### LinkerDriver::linkerMain

构建 parser

处理 parser

### LinkerDriver::link

#### Create output files

#### Handle --trace-symbol

`symtab.insert()`

#### Handle -u/--undefined before input files

`addUnusedUndefined()`

#### parseFile

Add symbols in File to the symbol table.

调用 `doParseFile()` ，对每类文件一一进行处理

* Binary file
* Lazy object file
* .so file
* LLVM bitcode file
* Regular object file

对 Binary File，调用 `BinaryFile::parse()`。为每个二进制文件创建相应符号（`symtab.addAndCheckDuplicate()`）。For each input file foo that is embedded to a result as a binary blob, we define _binary_foo_{start,end,size} symbols, so that user programs can access blobs by name.

对于 Regular object file，调用 `ObjFile<ELFT>::parse`

1. Read a section table
2. Handle dependent libraries and selection of section groups as these are not done in parallel
   1. Handle SHT_LLVM_DEPENDENT_LIBRARIES sh_type section
   2. Handle SHT_ARM_ATTRIBUTES sh_type section
   3. Handle SHT_GROUP sh_type section
3. Read a symbol table（`ObjFile<ELFT>::initializeSymbols`）
   1. Add global symbols to symtab
   2. Perform symbol resolution on non-local symbols
      1. Push back SHN_UNDEF symbols
      2. CommonSymbol（SHN_COMMON）
      3. Handle global defined symbols. Defined::section will be set in postParse
   3. Handle undefined symbols

##### `ObjFile<ELFT>::initializeSymbols`

`ArrayRef<Elf_Sym> eSyms = this->getELFSyms<ELFT>()`：获取 ELF section symbols

将全局符号放入全局符号表 `symtab`（Some entries have been filled by LazyObjFile）

若有重复定义，在 post parse 时，全局符号表中相关符号对应的文件一定会与文件的符号表中对应的文件不一致

调用 `resolve()` 刷新符号

#### post parse

Do post parse work like checking duplicate symbols.

对于 objectFiles

1. `ObjFile<ELFT>::initSectionsAndLocalSyms`
2. postParse

对于 bitcodeFiles

1. postParse

##### 初始化 sections and local symbols(`ObjFile<ELFT>::initSectionsAndLocalSyms`)

###### `ObjFile<ELFT>::initializeSections`

handle `-r`

handle SHF_LINK_ORDER sections

create SHT_REL[A] sections

###### initialize local symbols

new (symbols[i]) Undefined/Defined

##### postParse

This checks duplicate symbols and may do symbol property merge in the future.

遍历当前文件的符号，将符号放入 `ctx.duplicates` 中

1. 处理 STT_TLS symbol
2. 处理 non-COMMON defined symbol
3. 跳过未定义符号
4. 处理 Defined symbol
5. 跳过 STB_WEAK 符号
6. 符号重复定义

处理 Defined symbol

```cpp
if (sym.file == this) {
  cast<Defined>(sym).section = sec;
  continue;
}
```

跳过 STB_WEAK 符号

```cpp
if (sym.binding == STB_WEAK || binding == STB_WEAK)
  continue;
```

#### compileBitcodeFiles

Do link-time optimization.

#### replaceCommonSymbols

Replaces common symbols with defined symbols reside in .bss sections.

#### Aggregate sections

Aggregate all input sections into one place.

#### Strip sections

删除二进制文件中多余部分

## TODO

1. [ ] 梳理符号表的处理过程（主要在 parseFile？）
2. [ ] `getObjMsg` 的调用时刻，和 `initSectionsAndLocalSyms` 关系？（getObjMsg may be called before ObjFile::initSectionsAndLocalSyms where local symbols are initialized.）
3. [ ] ObjFile 类和其他类的关系
4. [ ] parallelForEach
5. [ ] STT_TLS
6. [ ] struct Ctx 和 CommonLinkerContext 的关系
7. [ ] SmallVector
8. [ ] StringRef
9. [ ] LTO
10. [ ] symbol 类型(common/...)
11. [ ] PLT / GOT
12. [ ] OutputSection
13. [ ] dyn_cast

## 参考链接

# Front End

## 参考链接

1. [用LLVM开发新语言](https://llvm-tutorial-cn.readthedocs.io/en/latest/index.html#)
2. [llvm入门教程-Kaleidoscope前端](https://zhuanlan.zhihu.com/p/430545662)

# LLVM IR

## 参考链接

1. [LLVM IR入门指南](https://evian-zhang.github.io/llvm-ir-tutorial/)
