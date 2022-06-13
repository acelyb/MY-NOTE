# C++ 基础

## 输入输出

to be continued...

## 变量和基本类型

### 变量

#### 变量定义

定义并初始化为0：

```cpp
int a = 0;
// C++11 列表初始化，无论是初始化对象还是某些时候为对象赋新值，
// 都可以使用这样一组由花括号括起来的初始值
int a = {0};
int a{0};
int a(0);
```

如果使用列表初始化且初始化存在丢失信息的风险，则编译器将报错：

```cpp
long double ld = 3.1215926536;
int a{ld}, b = {ld};    // 错误：转换未执行，因为存在丢失信息的危险
int c(ld), d = ld;      // 正确：转换执行，且确实丢失了部分值
```

#### 变量声明和定义的关系

为了支持分离式编译，C++ 将声明和定义区分开来。声明（declaration）使得名字为程序所知，一个文件如果想使用别处定义的名字则必须包含对那个名字的声明。而定义（definition）负责创建与名字关联的实体。

定义除了规定变量的类型和名字，还申请存储空间，也可能会为变量赋一个初始值。

```cpp
extern int i;   // 声明 i 而非定义 i
int j;          // 声明并定义 j
```

任何包含了显式初始化的声明即成为定义。

```cpp
extern double pi = 3.1416;  // 定义
```

在函数体内部，如果试图初始化一个由`extern`关键字标记的变量，将引发错误。

> 变量能且只能被定义一次，但可以被多次声明

### 复合类型

#### 引用

引用（reference）为对象起了另外一个名字，引用类型引用（refers to）另外一种类型。通过将声明符写成`&d`的形式来定义引用类型，其中`d`是声明的变量名：

```cpp
int ival = 1024;
int &refVal = ival;     // refVal 指向 ival（是 ival 的另一个名字）
int &refVal2;           // 报错：引用必须被初始化
```

一般在初始化变量时，初始值会被拷贝到新建的对象中。然而定义引用时，程序把引用和它的初始值绑定（bind）在一起，而不是将初始值拷贝给引用。

> 引用即别名

定义了一个引用后，对其进行的所有操作都是在与之绑定的对象上进行的：

```cpp
refVal = 2;         // 把2赋给 refVal 指向的对象，此处即是赋给了 ival
int ii = refVal;    // 与 ii = ival 执行的结果一样
```

#### 指针

指针（pointer）是“指向（point to）”另外一种类型的复合类型。

1. 指针本身就是一个对象，允许对指针赋值和拷贝，而且在指针的声明周期内它可以先后指向几个不同的对象
2. 指针无需在定义时赋值

定义指针类型的方法将声明符号写成`*d`的形式，其中`d`是变量名。如果在一条语句中定义了几个指针变量，每个变量前面都必须有符号`*`：

```cpp
int *ip1, *ip2;     // ip1 和 ip2 都是指向 int 型对象的指针
double dp, *dp2;    // dp2 是指向 double 型对象的指针，dp 是 double 型对象
```

因为引用不是对象，没有实际地址，所以不能定义指向引用的指针。

##### 指针值

指针的值（即地址）应属于下列4种状态之一：

1. 指向一个对象
2. 指向紧邻对象所占空间的下一个位置
3. 空指针，意味着指针没有指向任何对象
4. 无效指针，也就是上述情况之外的其他值

##### 赋值和指针

引用本身并非是一个对象，一旦定义了引用，就无法令其再绑定到另外的对象，之后每次使用这个引用都是访问它最初绑定的那个对象。而指针和它存放的地址之间并没有这种限制。

##### 其他指针操作

任何非0指针对应的条件值都是 true。

##### void* 指针

`void*`指针是一种特殊的指针类型，可用于存放任意对象的地址。

```cpp
double obj = 3.14, *pd = &obj;
void *pv = &pbj;    // 正确：void* 能存放任意类型对象的地址，obj 可以是任意类型的对象
pv = pd;            // pv 可以存放任意类型的指针
```

利用`void*`指针能做的事有限，不能直接操作`void*`指针所指向的对象，因为我们并不知道这个对象到底是什么类型，也就无法确定能在这个对象上做哪些操作。

#### 理解复合类型的声明

##### 指向指针的引用

引用本身不是有个对象，因此不能定义指向引用的指针。但指针是对象，所以存在对指针的引用：

```cpp
int i = 42;
int *p;
int *&r = p;    // r 是一个对指针 p 的引用
r = &i;         // r 引用了一个指针，因此给 r 赋值 &i 就是令 p 指向 i
*r = 0;         // 解引用 r 得到 i，也就是 p 指向的对象，将 i 的值改为0
```

要理解 r 的类型到底是什么，最简单的办法是从右向左阅读 r 的定义。离变量名最近的符号对变量的类型有最直接的影响，因此 r 是一个引用。声明符的其余部分用以确定 r 引用的类型是什么。声明的基本数据类型部分指出 r 引用的是一个 int 指针。

### const 限定符

默认状态下，const 对象仅在文件内有效

#### const 的引用

```cpp
const int ci = 1024;
const int &r1 = ci;     // 正确：引用及其对应的对象都是常量
r1 = 42;                // 错误：r1 是对常量的引用
int &r2 = ci;           // 错误：试图让一个非常量引用指向一个常量对象
```

```cpp
int i = 42;
int &r1 = i;        // 引用 ri 绑定对象 i
const int &r2 = i;  // r2 也绑定对象 i，但是不允许通过 r2 修改 i 的值
r1 = 0;             // r1 并非常量，i 的值修改为0
r2 = 0;             // 错误：r2 是一个常量引用
```

#### 指针和 const

类似于常量引用，指向常量的指针不能用于改变其所指对象的值。想要存放常量对象的地址，只能使用指向常量的指针：

```cpp
const double pi = 3.14;     // pi 是个常量，它的值不能改变
double *ptr = &pi;          // 错误：ptr 是一个普通指针
const double *cptr = &pi;   // 正确：cptr 可以指向一个双精度常量
*cptr = 42;                 // 错误：不能给 *cptr 赋值
```

允许令一个指向常量的指针指向一个非常量对象：

```cpp
double dval = 3.14;     // dval 是一个双精度浮点数，它的值可以改变
cptr = &dval;           // 正确：但是不能通过 cptr 改变 dval 的值
```

#### const 指针

常量指针（const pointer）必须初始化。一旦初始化完成，它的值（也就是存放在指针中的那个地址）就不能再改变。把`*`放在`const`关键字之前用以说明指针是一个常量，这样的书写形式隐含着一层意味，即不变的是指针本身的值而非指向的那个值：

```cpp
int errNumb = 0;
int *const curErr = &errNumb;   // curErr 将一直指向 errNumb
const double pi = 3.14159;
const double *const pip = &pi;  // pip 是一个指向常量对象的常量指针
```

指针本身是一个常量并不意味着不能通过指针改变其所指对象的值，能否这样做完全依赖于所指对象的类型。

#### constexpr 变量

将变量声明为 constexpr 类型以便由编译器来验证变量的值是否是一个常量表达式。声明为 cosntexpr 的变量一定是一个常量，而且必须用常量表达式初始化：

```cpp
constexpr int mf = 20;          // 20是常量表达式
constexpr int limit = mf + 1;   // mf + 1 是常量表达式
constexpr int sz = size();      // 只有当 size 是一个 constexpr 函数时才是一条正确的声明语句
```

一般来说，如果你认定变量是一个常量表达式，那就把它声明成 constexpr 类型

一个 constexpr 指针初始值必须是 nullptr 或者 0，或者是存储于某个固定地址中的对象

在 constexpr 声明中如果定义了一个指针，限定符 constexpr 仅对指针有效，与指针所指的对象无关：

```cpp
const int *p = nullptr;     // p 是一个指向整型常量的指针
constexpr int *q = nullptr; // q 是一个指向整数的常量指针
```

### 处理类型

#### 类型别名

两种方法可用于定于类型别名

```cpp
typedef double wages;       // wages 是 double 的同义词
typedef wages base, *p;     // base 是 double 的同义词，p 是 double* 的同义词

// 新标准规定了一种新的方法，使用别名声明（alias declaration）来定义类型的别名
using SI = Sales_item;      // SI 是 Sales_item 的同义词
```

```cpp
typedef char *pstring;
const pstring cstr = 0;     // cstr 是指向 char 的常量指针
const pstring *ps;          // ps 是一个指针，它的对象是指向 char 的常量指针
```

const 是对给定类型的修饰，pstring 实际上是指向 char 的指针，因此，const pstring 就是指向 char 的常量指针，而非指向常量字符的指针。

```cpp
const char *cstr = 0;   // 是对 const pstring cstr 的错误理解
```

声明语句中用到 pstring 时，其基本数据类型是指针。可是用 char* 重写了声明语句后，数据类型就变成了 char，`*`成为了声明符的一部分。这样改写的结果是，const char 成了基本数据类型。前后两种声明含义截然不同，前者声明了一个指向 char 的常量指针，改写后的形式则声明了一个指向 const char 的指针。

#### auto 类型说明符

auto 让编译器通过初始值来推算变量的类型。显然，auto 定义的的变量必须有初始值：

```cpp
// 由 val1 和 val2 相加的结果可以推断出 item 的类型
auto item = val1 + val2;
```

#### decltype 类型指示符

# C++11 新特性

## 类模板

### 定义类模板

```cpp
template <typename T> class Blob {
    public:
        typedef T value_type;
    private:
        std::shared_ptr<std::vector<T>> data;
};
```

### 实例化类模板

当使用一个类模板时，必须提供额外信息，这些额外信息是显示模板实参（explicit template argument）列表，它们被绑定到模板参数。编译器使用这些模板实参来实例化出特定的类。

例如，为了用`Blob`模板定义一个类型，必须提供元素类型：

```cpp
Blob<int> ia;       // 空 Blob<int>
Blob<int> ia2 = {0, 1, 2, 3, 4};    // 有5个元素的 Blob<int>
```

一个类模板的每个实例都形成一个独立的类。类型`Blob<string>`与任何其他`Blob`类型都没有关联，也不会对任何其他`Blob`类型的成员有特殊访问权限。

### 在模板作用域中引用模板类型

通常将模板自己的参数当作被使用模板的实参

```cpp
std::shared_ptr<std::vector<T>> data;
```

当实例化一个特定类型的`Blob`，例如`Blob<string>`时，`data`会成为

```cpp
shared_ptr<vector<string>>
```

### 类模板的成员函数

类模板的成员函数具有和模板相同的模板参数。定义在类模板之外的成员函数必须以关键字`template`开始，后接类模板参数列表。

在类外定义一个成员时，必须说明成员属于哪个类。而且，从一个模板生成的类的名字中必须包含其模板实参。当我们定义一个成员函数时，模板实参与模板形参相同。即，对于`StrBlob`的一个给定的成员函数

```cpp
ret-type StrBlob::member-name(parm-list)
```

对应的`Blob`的成员应该是这样的：

```cpp
template <typename T>
ret-type Blob<T>::member-name(parm-list)
```

### 在类代码内部简化模板类名的使用

在类模板自己的作用域中，我们可以直接使用模板名而不提供实参
590
