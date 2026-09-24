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

##### 函数指针

函数存放在内存的代码区域内，它们同样有地址。如果我们有一个 `int test(int a)` 的函数，那么，它的地址就是函数的名字，这一点如同数组一样，数组的名字就是数组的起始地址

函数指针的定义方式

```cpp
data_types (*func_pointer)( data_types arg1, data_types arg2, ...,data_types argn);

int (*fp)(int a); // 这里就定义了一个指向函数(这个函数参数仅仅为一个 int 类型，函数返回值是 int 类型)的指针 fp
```

```cpp
int test(int a)
{
    return a;
}
int main(int argc, const char * argv[])
{
    
    int (*fp)(int a);
    fp = test;
    cout<<fp(2)<<endl;
    return 0;
}
```

**注意：**函数指针所指向的函数一定要保持函数的返回值类型，函数参数个数，类型一致

typedef 定义可以简化函数指针的定义

```cpp
int test(int a)
{
    return a;
}
 
int main(int argc, const char * argv[])
{
    
    typedef int (*fp)(int a);
    fp f = test;
    cout<<f(2)<<endl;
    return 0;
}
```

把函数作为参数传入另一个函数

```cpp
#include <iostream>
template <typename T>
bool ascending(T x, T y) {
    return x > y; 
}
template <typename T>
bool descending(T x, T y) {
    return x < y;
}
template<typename T>
void bubblesort(T *a, int n, bool(*cmpfunc)(T, T)){
    bool sorted = false;
    while(!sorted){
        sorted = true;
        for (int i=0; i<n-1; i++)
            if (cmpfunc(a[i], a[i+1])) {
                std::swap(a[i], a[i+1]);
                sorted = false;
            }
        n--;
    }
}

int main()
{
    int a[8] = {5,2,5,7,1,-3,99,56};
    int b[8] = {5,2,5,7,1,-3,99,56};

    bubblesort<int>(a, 8, ascending);

    for (auto e:a) std::cout << e << " ";
    std::cout << std::endl;

    bubblesort<int>(b, 8, descending);

    for (auto e:b) std::cout << e << " ";

    return 0;
}
// -3 1 2 5 5 7 56 99 
// 99 56 7 5 5 2 1 -3 [Finished in 0.4s]
```

设置默认函数

```cpp
void bubblesort(T *a, int n, bool(*cmpfunc)(T, T) = ascending)
```

利用函数指针，我们可以构成函数指针数组，更明确点的说法是构成指向函数的指针数组

```cpp
void t1(){cout<<"test1"<<endl;}
void t2(){cout<<"test2"<<endl;}
void t3(){cout<<"test3"<<endl;}
 
int main(int argc, const char * argv[])
{
    
    typedef void (*fp)(void);
    fp b[] = {t1,t2,t3}; // b[] 为一个指向函数的指针数组
    b[0](); // 利用指向函数的指针数组进行下标操作就可以进行函数的间接调用了
    
    return 0;
}
```

类成员函数指针（member function pointer），是 C++ 语言的一类指针数据类型，用于存储一个指定类具有给定的形参列表与返回值类型的成员函数的访问信息

基本上要注意的有两点：

* 函数指针赋值要使用 &
* 使用 `.*(实例对象)` 或者 `->*（实例对象指针）` 调用类成员函数指针所指向的函数

类成员函数指针指向类中的非静态成员函数

对于 nonstatic member function （非静态成员函数）取地址，获得该函数在内存中的实际地址

对于 virtual function（虚函数）, 其地址在编译时期是未知的，所以对于 virtual member function（虚成员函数）取其地址，所能获得的只是一个索引值

```cpp
//指向类成员函数的函数指针
#include <iostream>
#include <cstdio>
using namespace std;
 
class A
{
    public:
        A(int aa = 0):a(aa){}
 
        ~A(){}
 
        void setA(int aa = 1)
        {
            a = aa;
        }
        
        virtual void print()
        {
            cout << "A: " << a << endl;
        }
 
        virtual void printa()
        {
            cout << "A1: " << a << endl;
        }
    private:
        int a;
};
 
class B:public A
{
    public:
        B():A(), b(0){}
        
        B(int aa, int bb):A(aa), b(bb){}
 
        ~B(){}
 
        virtual void print()
        {
            A::print();
            cout << "B: " << b << endl;
        }
 
        virtual void printa()
        {
            A::printa();
            cout << "B: " << b << endl;
        }
    private:
        int b;
};
 
int main(void)
{
    A a;
    B b;
    void (A::*ptr)(int) = &A::setA;
    A* pa = &a;
    
    //对于非虚函数，返回其在内存的真实地址
    printf("A::set(): %p\n", &A::setA);
    //对于虚函数， 返回其在虚函数表的偏移位置
    printf("B::print(): %p\n", &A::print);
    printf("B::print(): %p\n", &A::printa);
 
    a.print();
 
    a.setA(10);
 
    a.print();
 
    a.setA(100);
 
    a.print();
    //对于指向类成员函数的函数指针，引用时必须传入一个类对象的this指针，所以必须由类实体调用
    (pa->*ptr)(1000);
 
    a.print();
 
    (a.*ptr)(10000);
 
    a.print();
    return 0;
}
```

执行以上代码，输出结果为：

```bash
A::set(): 0x8048a38
B::print(): 0x1
B::print(): 0x5
A: 0
A: 10
A: 100
A: 1000
A: 10000
```

类成员函数指针指向类中的静态成员函数

```cpp
#include <iostream>
using namespace std;
 
class A{
public:
    
    //p1是一个指向非static成员函数的函数指针
    void (A::*p1)(void);
    
    //p2是一个指向static成员函数的函数指针
    void (*p2)(void);
    
    A(){
        /*对
         **指向非static成员函数的指针
         **和
         **指向static成员函数的指针
         **的变量的赋值方式是一样的，都是&ClassName::memberVariable形式
         **区别在于：
         **对p1只能用非static成员函数赋值
         **对p2只能用static成员函数赋值
         **
         **再有，赋值时如果直接&memberVariable，则在VS中报"编译器错误 C2276"
         **参见：http://msdn.microsoft.com/zh-cn/library/850cstw1.aspx
         */
        p1 =&A::funa; //函数指针赋值一定要使用 &
        p2 =&A::funb;
        
        //p1 =&A::funb;//error
        //p2 =&A::funa;//error
        
        //p1=&funa;//error,编译器错误 C2276
        //p2=&funb;//error,编译器错误 C2276
    }
    
    void funa(void){
        puts("A");
    }
    
    static void funb(void){
        puts("B");
    }
};
 
int main()
{
    A a;
    //p是指向A中非static成员函数的函数指针
    void (A::*p)(void);
    
    (a.*a.p1)(); //打印 A
    
    //使用.*(实例对象)或者->*（实例对象指针）调用类成员函数指针所指向的函数
    p = a.p1;
    (a.*p)();//打印 A
    
    A *b = &a;
    (b->*p)(); //打印 A
    
    /*尽管a.p2本身是个非static变量,但是a.p2是指向static函数的函数指针，
     **所以下面这就话是错的!
     */
//    p = a.p2;//error
    
    void (*pp)(void);
    pp = &A::funb;
    pp(); //打印 B
    
    return 0;
}
```

类成员函数指针与普通函数指针不是一码事。前者要用 .*与 ->* 运算符来使用，而后者可以用 * 运算符（称为"解引用"dereference，或称"间址"indirection）

普通函数指针实际上保存的是函数体的开始地址，因此也称"代码指针"，以区别于 C/C++ 最常用的数据指针

而类成员函数指针就不仅仅是类成员函数的内存起始地址，还需要能解决因为 C++ 的多重继承、虚继承而带来的类实例地址的调整问题，所以类成员函数指针在调用的时候一定要传入类实例对象

**参考链接**

1. [深入浅出——理解c/c++函数指针](https://zhuanlan.zhihu.com/p/37306637)
2. [C++ 函数指针 & 类成员函数指针](https://www.runoob.com/w3cnote/cpp-func-pointer.html)

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

const 与 constexpr 变量之间的主要 difference（区别）是，const 变量的初始化可以推迟到运行时进行。 constexpr 变量必须在编译时进行初始化。 所有的 constexpr 变量都是 const

A constexpr specifier used in an object declaration implies const.

这里的object你可以理解为变量，意思是 constexpr 修饰的变量都会隐式添加一个 const 限定符。即 constexpr 添加的是顶层 const

也就是说：

```cpp
// T 是任意类型
constexpr T a = xxx;
// 不考虑其他因素，在类型上等价于：
T const a = xxx;
```

T 实际上可以填任意类型，包括指针

```cpp
// 原本的代码
constexpr char *msg = "Hello, world!";
// 实际上的效果，并非 const char *
char * const msg = "Hello, world!";
```

下面一行的 msg 实际上是一个指向 char 的指针常量，而我们可以通过它任意修改被指向的字符串（当然这是未定义行为）。指针常量意味着我们不能把这个指针重新指向其他的对象，这个 const 作用在指针本身上，因此叫做顶层 const

而字符串常量的类型是`const char[N]`，在表达式里退化为`const char *`，这表示一个指向常量字符串的指针，这里的 const 的底层的，因为它作用于被指向的对象而不是我们的指针自身

constexpr 不是 const 的等价替代品，它只会添加顶层 const，不会添加底层 const

所以 constexpr 的字符串常量应该这样写：

```cpp
constexpr const char *p = "Hello, world!";
```

或者你的编译环境支持c++17，我更推荐你这样写：

```cpp
#include <string_view>
 
constexpr std::string_view msg = "Hello, world!";
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
