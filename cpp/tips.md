# const 相关

## 函数名后加 const

只有类的成员函数才能在函数名后面加上const，这时成员函数叫做常量成员函数。

常量成员函数在执行期间不能修改成员变量的值（静态成员变量除外），也不能调用同类的非常量成员函数（同样的静态成员函数除外）。

增强健壮性。

常成员函数说明格式：类型说明符  函数名（参数表）const;

这里，const 是函数类型的一个组成部分，因此在实现部分也要带 const 关键字。

const 关键字可以被用于参与对重载函数的区分

通过常对象只能调用它的常成员函数

```cpp
class Sample{
    public:
        int value;
        void GetValue() const;
        void func() {};
        Sample() { value = 0; }
};

void Sample::GetValue() const {
    value = 0;  // 错误，常量成员函数不能修改成员变量的值
    func();     // 错误，常量成员函数不能调用非常量成员函数
}

int main(void) {
    const Sample s;
    s.value = 1;    // 错误，常量对象不能被修改
    s.func();       // 错误，常量对象上面不能执行非常量成员函数，即使这个成员函数为空
    s.GetValue();   // 正确，常量对象上面可以执行常量函数
    return 0;
}
```

注：

1. 非静态成员函数后才能加 const，加到非成员函数或静态成员后面会产生编译错误。
2. 表示成员函数隐含传入的this指针为 const 指针，决定了在该成员函数中，任意修改它所在的类的成员的操作都是不允许的（因为隐含了对this指针的 const 引用），唯一的例外是对于 mutable 修饰的成员。
3. 调用
   * 加了 const 的成员函数可以被非 const 对象和 const 对象调用
   * 不加 const 的成员函数只能被非 const 对象调用

## 常对象

常类型的对象必须进行初始化，而且不能被更新。

* 常引用：被引用的对象不能被更新。
const  类型说明符  &引用名
* 常对象：必须进行初始化,不能被更新。
类名  const  对象名
* 常数组：数组元素不能被更新。
类型说明符  const  数组名[大小]...
* 常指针：指向常量的指针。

# static 相关

## 静态成员函数

类外代码可以使用类名和作用域操作符来调用静态成员函数。静态成员函数只能引用属于该类的静态数据成员或静态成员函数。

```CPP
class Application {
 public:
  static void f();
  static void g();

 private:
  static int global;
};
int Application::global = 0;
void Application::f() { global = 5; }
void Application::g() { cout << global << endl; }

int main() {
  Application::f();
  Application::g();
  system("pause");
  return 0;
}
```

```cpp
class A {
 public:
  static void f(A a);

 private:
  int x;
};
void A::f(A a) {
  //静态成员函数只能引用属于该类的静态数据成员或静态成员函数。
  // cout<<x; //对x的引用是错误的
  cout << a.x;  //正确
}

int main(int argc, char const *argv[]) {
  A a;
  a.f(A());
  system("pause");
  return 0;
}
```

## 静态数据成员

静态数据成员用关键字static声明，该类的所有对象维护该成员的同一个拷贝。必须在类外定义和初始化，用(::)来指明所属的类。

```cpp
class Point {
 public:
  Point(int xx = 0, int yy = 0) {
    X = xx;
    Y = yy;
    countP++;
  }
  Point(Point &p);
  int GetX() { return X; }
  int GetY() { return Y; }
  void GetC() { cout << " Object id=" << countP << endl; }

 private:
  int X, Y;
  //静态数据成员，必须在外部定义和初始化，内部不能直接初始化！
  static int countP;
};
Point::Point(Point &p) {
  X = p.X;
  Y = p.Y;
  countP++;
}
//必须在类外定义和初始化，用(::)来指明所属的类。
int Point::countP = 0;
int main() {
  Point A(4, 5);
  cout << "Point A," << A.GetX() << "," << A.GetY();
  A.GetC();
  Point B(A);
  cout << "Point B," << B.GetX() << "," << B.GetY();
  B.GetC();
  system("pause");
  return 0;
}
```

# 类相关

## 类对象的构造

先构造成员，再构造自身（调用构造函数）

## 派生类构造函数

派生类可能有多个基类，也可能包括多个成员对象，在创建派生类对象时，派生类的构造函数除了要负责本类成员的初始化外，还要调用基类和成员对象的构造函数，并向它们传递参数，以完成基类子对象和成员对象的建立和初始化。

**派生类只能采用构造函数初始化列表的方式向基类或成员对象的构造函数传递参数**，形式如下：

派生类构造函数名(参数表):基类构造函数名(参数表),成员对象名1(参数表),…{
    //……
}

## 初始化

构造函数参数列表初始化与直接在函数内部初始化的区别：

1. 分配memory给对象base
2. 调用类Base相应的构造函数
3. 先进行初始化列表的初始化
4. 再进入构造函数体内，进行一些赋值
5. 跳出函数体，控制权还给调用者

函数体内再赋值是重复的，低效的，一般建议成员列表初始化

C++中，子类实例化时若没有特殊声明，会先自动调用父类的默认构造函数，再点用自己的。如果子类对象初始化时想显式调用其它父类的构造函数对父类成员进行初始化，C++规定，可以在子类的初始化列表中，像列表初始化其他成员函数一样在冒号后面“call”所需要的父类的构造函数

C++也不允许在列表中直接对父类变量进行初始化，但允许在函数体中进行对的赋值，不过这样比较危险。所以在子类列表初始化时“调用”父类的某个构造函数，是最符合规范的

## 构造函数和析构函数调用次序

### 派生类对象构造

* 先构造基类
* 再构造成员
* 最后构造自身（调用构造函数）

基类构造顺序由派生层次决定：**最远的基类最先构造**

成员构造顺序和定义顺序符合

析构函数的析构顺序与构造相反

### 基类与派生类对象的关系

基类对象与派生类对象之间存在赋值相容性。包括以下几种情况：

* 把派生类对象赋值给基类对象
* 把派生类对象的地址赋值给基类指针
* 用派生类对象初始化基类对象的引用

反之则不行，即不能把基类对象赋值给派生类对象；不能把基类对象的地址赋值给派生类对象的指针；也不能把基类对象作为派生对象的引用。

## 继承

### 公有继承

1. 基类中 protected 的成员
   1. 类内部：可以访问
   2. 类的使用者：不能访问
   3. 类的派生类成员：可以访问
2. 派生类不可访问基类的 private 成员
3. 派生类可以访问基类的 protected 成员
4. 派生类可访问基类的 public 成员

| 基类 | public 继承 | 派生类 |
| :---: | :---: | :---: |
| public | ---> | public |
| protected | ---> | protected |
| private | ---> | 不可访问 |

### 私有继承

派生类也不可访问基类的 private 成员

| 基类 | private 继承 | 派生类 |
| :---: | :---: | :---: |
| public | ---> | private |
| protected | ---> | private |
| private | ---> | 不可访问 |

### 保护继承

派生方式为 protected 的继承称为保护继承，在这种继承方式下，基类的 public 成员在派生类中会变成 protected 成员，基类的 protected 和 private 成员在派生类中保持原来的访问权限

注意：当采用保护继承的时候，由于 public 成员变为 protected 成员，因此类的使用者不可访问，而派生类可以访问

| 基类 | protected 继承 | 派生类 |
| :---: | :---: | :---: |
| public | ---> | protected |
| protected | ---> | protected |
| private | ---> | 不可访问 |

### 派生类对于基类成员的访问形式

1. 通过派生类对象直接访问基类成员
2. 在派生类成员函数中直接访问基类成员
3. 通过基类名字限定访问被重载的基类成员名

## 友元

友元函数是在类声明中由关键字friend修饰说明的非成员函数，在它的函数体中能够通过对象名访问 private 和 protected成员作用：增加灵活性，使程序员可以在封装和快速性方面做合理选择。访问对象中的成员必须通过对象名。

若一个类为另一个类的友元，则此类的所有成员都能访问对方类的私有成员。声明语法：将友元类名在另一个类中使用friend修饰说明。

如果声明B类是A类的友元，B类的成员函数就可以访问A类的私有和保护数据，但A类的成员函数却不能访问B类的私有、保护数据。

```cpp
class A {
  friend class B;

 public:
  void Display() { cout << x << endl; }

 private:
  int x;
};
class B {
 public:
  void Set(int i);
  void Display();

 private:
  A a;
};
void B::Set(int i) { a.x = i; }
void B::Display() { a.Display(); }

int main(int argc, char const *argv[]) {
  B b;
  b.Set(10);
  b.Display();

  system("pause");
  return 0;
}
```

友元是C++提供的一种破坏数据封装和数据隐藏的机制。通过将一个模块声明为另一个模块的友元，一个模块能够引用到另一个模块中本是被隐藏的信息。可以使用友元函数和友元类。为了确保数据的完整性，及数据封装与隐藏的原则，建议尽量不使用或少使用友元。

## 调用规则

当同时存在直接基类和间接基类时，每个派生类只负责其直接基类的构造。

## 构造函数和析构函数的构造规则

### 派生类可以不定义构造函数的情况

* 当具有下述情况之一时，派生类可以不定义构造函数。
* 基类没有定义任何构造函数。
* 基类具有缺省参数的构造函数。
* 基类具有无参构造函数。

### 派生类必须定义构造函数的情况

* 当基类或成员对象所属类只含有带参数的构造函数时，即使派生类本身没有数据成员要初始化，它也必须定义构造函数，并以构造函数初始化列表的方式向基类和成员对象的构造函数传递参数，以实现基类子对象和成员对象的初始化。

### 派生类的构造函数只负责直接基类的初始化

C++语言标准有一条规则：如果派生类的基类同时也是另外一个类的派生类，则每个派生类只负责它的直接基类的构造函数调用。

这条规则表明当派生类的直接基类只有带参数的构造函数，但没有默认构造函数时（包括缺省参数和无参构造函数），它必须在构造函数的初始化列表中调用其直接基类的构造函数，并向基类的构造函数传递参数，以实现派生类对象中的基类子对象的初始化。

这条规则有一个例外情况，当派生类存在虚基类时，所有虚基类都由最后的派生类负责初始化。

### 总结

1. 当有多个基类时，将按照它们在继承方式中的声明次序调用，与它们在构造函数初始化列表中的次序无关。当基类A本身又是另一个类B的派生类时，则先调用基类B的构造函数，再调用基类A的构造函数。
2. 当有多个对象成员时，将按它们在派生类中的声明次序调用，与它们在构造函数初始化列表中的次序无关。
3. 当构造函数初始化列表中的基类和对象成员的构造函数调用完成之后，才执行派生类构造函数体中的程序代码。

```cpp
// 当同时存在直接基类和间接基类时，每个派生类只负责其直接基类的构造。
class A {
  int x;

 public:
  A(int aa) {
    x = aa;
    cout << "Constructing A" << endl;
  }
  ~A() { cout << "Destructing A" << endl; }
};
class B : public A {
 public:
  B(int x) : A(x) { cout << "Constructing B" << endl; }
};
class C : public B {
 public:
  C(int y) : B(y) { cout << "Constructing C" << endl; }
};
int main() {
  C c(1);
  system("pause");
}
```

## 虚拟继承

多继承下的二义性：在多继承方式下，派生类继承了多个基类的成员，当两个不同基类拥有同名成员时，容易产生名字冲突问题。

虚拟继承引入的原因：重复基类，派生类间接继承同一基类使得间接基类（Person）在派生类中有多份拷贝，引发二义性。

### 虚拟继承 virtual inheritance 的定义

#### 语法

class derived_class : virtual […] base_class

虚基类virtual base class

被虚拟继承的基类在其所有的派生类中，仅出现一次

#### 虚拟继承的构造次序

虚基类的初始化与一般的多重继承的初始化在语法上是一样的，但构造函数的调用顺序不同

若基类由虚基类派生而来，则派生类必须提供对间接基类的构造（即在构造函数初始列表中构造虚基类，无论此虚基类是直接还是间接基类）

调用顺序的规定：

* 先调用虚基类的构造函数，再调用非虚基类的构造函数
* 若同一层次中包含多个虚基类,这些虚基类的构造函数按它们的说明的次序调用
* 若虚基类由非基类派生而来,则仍然先调用基类构造函数,再调用派生类构造函数

#### 虚基类由最终派生类初始化

在没有虚拟继承的情况下，每个派生类的构造函数只负责其直接基类的初始化。但在虚拟继承方式下，虚基类则由最终派生类的构造函数负责初始化。

在虚拟继承方式下，若最终派生类的构造函数没有明确调用虚基类的构造函数，编译器就会尝试调用虚基类不需要参数的构造函数（包括缺省、无参和缺省参数的构造函数），如果没找到就会产生编译错误。

## 多态性

多态性：多态就是在同一个类或继承体系结构的基类与派生类中，用同名函数来实现各种不同的功能

**静态绑定又称静态联编**，是指在编译程序时就根据调用函数提供的信息，把它所对应的具体函数确定下来，即在编译时就把调用函数名与具体函数绑定在一起。

**动态绑定又称动态联编**，是指在编译程序时还不能确定函数调用所对应的具体函数，只有在程序运行过程中才能够确定函数调用所对应的具体函数，即在程序运行时才把调用函数名与具体函数绑定在一起。

编译时多态性：---静态联编(连接)----系统在编译时就决定如何实现某一动作，即对某一消息如何处理。静态联编具有执行速度快的优点。在 C++ 中的编译时多态性是通过函数重载和运算符重载实现的。

运行时多态性：---动态联编(连接)----系统在运行时动态实现某一动作，即对某一消息在运行过程实现其如何响应。动态联编为系统提供了灵活和高度问题抽象的优点，在 C++ 中的运行时多态性是通过继承和虚函数实现的。

## 虚函数

### 基类与派生类的赋值相容

* 派生类对象可以赋值给基类对象。
* 派生类对象的地址可以赋值给指向基类对象的指针。
* 派生类对象可以作为基类对象的引用。

赋值相容的问题：不论哪种赋值方式，都只能通过基类对象（或基类对象的指针或引用）访问到派生类对象从基类中继承到的成员， 不能借此访问派生类定义的成员。

### 虚函数使得可以通过基类对象的指针或引用访问派生类定义的成员

### Virtual 关键字其实质是告知编译系统，被指定为 virtual 的函数采用动态联编的形式编译

### 虚函数的虚特征

基类指针指向派生类的对象时，通过该指针访问其虚函数将调用派生类的版本

* 一旦将某个成员函数声明为虚函数后，它在继承体系中就永远为虚函数
* 如果基类定义了虚函数，当通过基类指针或引用调用派生类对象时，将访问到它们实际所指对象中的虚函数版本
* 只有通过基类对象的指针和引用访问派生类对象的虚函数时，才能体现虚函数的特性
* 派生类中的虚函数要保持其虚特征，必须与基类虚函数的函数原型完全相同，否则就是普通的重载函数，与基类的虚函数无关
* 派生类通过从基类继承的成员函数调用虚函数时，将访问到派生类中的版本
* 只有类的非静态成员函数才能被定义为虚函数，类的构造函数和静态成员函数不能定义为虚函数。原因是虚函数在继承层次结构中才能够发生作用，而构造函数、静态成员是不能够被继承的
* 内联函数也不能是虚函数。因为内联函数采用的是静态联编的方式，而虚函数是在程序运行时才与具体函数动态绑定的，采用的是动态联编的方式，即使虚函数在类体内被定义，C++ 编译器也将它视为非内联函数

### 基类析构函数几乎总是为虚析构函数

假定使用 delete 和一个指向派生类的基类指针来销毁派生类对象，如果基类析构函数不为虚,就如一个普通成员函数，delete 函数调用的就是基类析构函数。在通过基类对象的引用或指针调用派生类对象时，将致使对象析构不彻底

## 纯虚函数和抽象类

**纯虚函数**：仅定义函数原型而不定义其实现的虚函数

```cpp
class X {
  virtual ret_type func_name (param) = 0;
}
```

**抽象类**：包含一个或多个纯虚函数的类

抽象类不能被实例化，但可以定义抽象类的指针和引用

定义一个抽象类的派生类意味着定义所有纯虚函数

C++ 对抽象类的限定：

* 抽象类中含有纯虚函数，由于纯虚函数没有实现代码，所有不能建立抽象类的对象
* 抽象类只能作为其他类的基类，可以通过抽象类对象的指针或引用和访问到它的派生类对象，实现运行时的多态
* 如果派生类只是简单地继承了抽象类的纯虚函数，而没有重新定义基类的纯虚函数，则派生类也是一个抽象类

## explicit

在C++中，explicit关键字用来修饰类的构造函数，被修饰的构造函数的类，不能发生相应的隐式类型转换，只能以显示的方式进行类型转换

explicit使用注意事项:

* explicit 关键字只能用于类内部的构造函数声明上
* explicit 关键字作用于单个参数的构造函数
* 在 C++ 中，explicit 关键字用来修饰类的构造函数，被修饰的构造函数的类，不能发生相应的隐式类型转换
* 类的声明和定义分别在两个文件中时，explicit只能写在在声明中，不能写在定义中

```cpp
#include <iostream>  
using namespace std;  
class Test1  
{  
public :  
    Test1(int num):n(num){}  
private:  
    int n;  
};  
class Test2  
{  
public :  
    explicit Test2(int num):n(num){}  
private:  
    int n;  
};  
  
int main()  
{  
    Test1 t1 = 12;  
    Test2 t2(13);  
    Test2 t3 = 14;  
          
    return 0;  
}
```

编译时，会指出 t3那一行error:无法从“int”转换为“Test2”。而t1却编译通过。注释掉t3那行，调试时，t1已被赋值成功


# 模板

## 函数模板

### 函数模板的特化

针对模板不能处理的特殊数据类型，编写与模板同名的特殊函数专门处理这些数据类型

形式：

```cpp
template <> 返回类型 函数名<特化的数据类型>(参数表) {
  ...
}
```

* template <> 是模板特化的关键字，<> 中不需要任何内容
* 函数名后的 <> 是需要特化处理的数据类型

### 说明

* 当程序中同时存在模板和它的特化时，特化将被优先调用
* 在同一个程序中，除了函数模板和它的特化外，还可以有同名的普通函数。其区别在于C++会对普通函数的调用实参进行隐式的类型转换，但不会对模板函数及特化函数的参数进行任何形式的类型转换

### 调用顺序

当同一程序中具有模板与普通函数时，其匹配顺序如下：

1. 完全匹配的非模板函数
2. 完全匹配的模板函
3. 类型相容的非模板函数

## 类模板

### 非类型参数

非类型参数是指某种具体的数据类型，在调用模板时只能为其提供用相应类型的常数值。非类型参数是受限制的，通常可以是整型、枚举型、对象或函数的引用，以及对象、函数或类成员的指针，**但不允许用浮点型（或双精度型）、类对象或void作为非类型参数**。

在下面的模板参数表中，T1、T2是类型参数，T3是非类型参数。

```cpp
template<class T1,class T2,int T3>
```

在实例化时，必须为T1、T2提供一种数据类型，为T3指定一个整常数（如10），该模板才能被正确地实例化。

### 特化

类模板有两种特化方式：一种是特化整个类模板，另一种是特化个别成员函数

特化类模板：

```cpp
template<>  void Array<char *>::Sort(){
    for(int i=0;i<Size-1;i++){
        int p=i;
        for(int j=i+1;j<Size;j++)
            if(strcmp(a[p],a[j])<0)
                p=j;
        char* t=a[p];
        a[p]=a[i];
        a[i]=t;
    }
}
```

特化成员函数：

```c++
template <> 返回类型 类模板名<特化的数据类型>::特化成员函数名(参数表){
  ...   //函数定义体
}
```

# 输入

用cin输入字符串数据时，如果字符串中含有空白就不能完整输入。因为遇到空白字符时，cin就认为字符串结束了

## 用函数get和getline读取数据

用法：`a = cin.get()` 或者 `cin.get(a)`

结束条件：输入字符足够后回车

说明：这个是单字符的输入，用途是输入一个字符，把它的ASCALL码存入到a中

处理方法：与cin不同，cin.get()在缓冲区遇到[enter]，[space]，[tab]不会作为舍弃，而是继续留在缓冲区中

### get()

#### get()两个参数

`cin.get(arrayname,size)`把字符输入到arrayname中，长度不超过size

#### get()三个参数

用法：cin.get(arrayname,size,s) ?把数据输入到arrayname字符数组中，当到达长度size时结束或者遇到字符s时结束

注释：a必须是字符数组，即char a[]l类型，不可为string类型；size为最大的输入长度；s为控制，遇到s则当前输入结束缓存区里的s将被舍弃

### 区别

* cin.get(arrayname,size)当遇到[enter]时会结束目前输入，他不会删除缓冲区中的[enter]
* cin.getline(arrayname,size)当遇到[enter]时会结束当前输入，但是会删除缓冲区中的[enter]

## extern "C"

在我们创建 DLL 工程的时候，常会看到在 dll 头文件要导出的函数声明中有 extern "C" 关键字。

只有在编写 C++ 代码的时候才应使用这个修饰符，在编写C代码的时候不用此修饰符。因为 C++ 编译器经常会对函数名和变量名称在编译的时候进行不可察觉的改变(mangle)，而这在函数连接的时候就会导致严重的问题。例如，dll 库是作者使用 C++ 编写的，而测试的程序是由 C 语言编写的，那么在编译的过程中，dll 库中的函数名会被编译器进行改变，但由 C 语言所写的测试程序并不会被改变，那么在连接器试图连接可执行文件的时候，会发现可执行文件引用了一个并不存在的符号而报错。extern "C" 的作用就是告诉编译器，不要对 C++ 代码的函数进行改变。

所以在混合使用 C 语言和 C++ 编程的时候一定要使用`extern "C"`修饰。

# 函数

## 动态调用 dlopen + dlsym

参考:
1. [博客1](https://www.cnblogs.com/sleepylulu/p/12029467.html)
2. [博客2](http://c.biancheng.net/view/8044.html)

## decltype

`decltype`被称作类型说明符，它的作用是选择并返回操作数的数据类型

### decltype + 变量

当使用`decltype(var)`的形式时，`decltype`会直接返回变量的类型

```cpp
const int ci = 0, &cj = ci;

// x的类型是const int
decltype(ci) x = 0;

// y的类型是const int &
decltype(cj) y = x;
```

### decltype + 表达式

当使用`decltype(expr)`的形式时，`decltype`会返回表达式结果对应的类型

```cpp
int i = 42, *p = &i, &r = i;

// r + 0是一个表达式
// 算术表达式返回右值
// b是一个int类型
decltype(r + 0) b;

// c是一个int &
decltype(*p) c = i;
```

### decltype + 函数

我们可以使用`decltype`获得函数`add_to`的类型（`add_to`定义见“函数类型”）：

```cpp
decltype(add_to) *pf = add_to;
```

当使用`decltype(func_name)`的形式时，`decltype`会返回对应的函数类型，不会自动转换成相应的函数指针

参考[博客](https://blog.csdn.net/u014609638/article/details/106987131/)

## 函数类型

主要作用是为了定义函数指针

```cpp
// 声明了一个函数类型
using FuncType = int(int &, int);

// 下面的函数就是上面的类型
int add_to(int &des, int ori);

// 声明了一个FuncType类型的指针
// 并使用函数add_to初始化
FuncType *pf = add_to;

int a = 4;

// 通过函数指针调用add_to
pf(a, 2);
```

## main 函数

### 参数

`int argc, char** argv` 中，`argc` 是命令行总的参数个数。`argv[]` 为保存命令行参数的字符串指针，其中第 0 个参数是程序的全名，以后的参数为命令行后面跟的用户输入的参数，argv参数是字符串指针数组，其各元素值为命令行中各字符串(参数均按字符串处理)的首地址。 指针数组的长度即为参数个数argc。数组元素初值由系统自动赋予

例如，输入 `test a.c b.c t.c`，则

```cpp
argc = 4

argv[0] = "test"  
argv[1] = "a.c"  
argv[2] = "b.c"  
argv[3] = "t.c"
```

## operator 重载运算符

operator 是 C++ 的一个关键字，它和运算符（如 =）一起使用，表示一个运算符重载函数，在理解时可将 operator 和待重载的运算符整体（如 operator=）视为一个函数名

实现运算符重载的方式通常有以下两种：

* 运算符重载实现为类的成员函数；
* 运算符重载实现为非类的成员函数（即全局函数）。

### 运算符重载实现为类的成员函数

在类体中声明（定义）需要重载的运算符，声明方式跟普通的成员函数一样，只不过运算符重载函数的名字是“operator紧跟一个 C++ 预定义的操作符”，示例用法如下（person 是我们定义的类）：

```cpp
bool operator==(const person& ps)
{
    if (this->age == ps.age)
    {
        return true;
    }
    return false;
}
```

### 运算符重载实现为非类的成员函数（即全局函数）

对于全局重载运算符，代表左操作数的参数必须被显式指定

```cpp
#include <iostream>
 
using namespace std;
 
class person
{
public:
    int age;
};
 
// 左操作数的类型必须被显式指定
// 此处指定的类型为person类
bool operator==(person const& p1 ,person const& p2)
{
    if (p1.age == p2.age)
    {
        return true;
    }
    else
    {
        return false;
    }
}
 
int main()
{
    person p1;
    person p2;
    p1.age = 18;
    p2.age = 18;
 
    if (p1 == p2)
    {
        cout << "p1 is equal with p2." << endl;
    }
    else
    {
        cout << "p1 is NOT equal with p2." << endl;
    }
 
    return 0;
}
```

### 运算符重载的方式选择

可以根据以下因素，确定把一个运算符重载为类的成员函数还是全局函数：

* 如果一个重载运算符是类的成员函数，那么只有当与它一起使用的左操作数是该类的对象时，该运算符才会被调用；而如果该运算符的左操作数确定为其他的类型，则运算符必须被重载为全局函数；
* C++ 要求'='、'[]'、'()'、'->'运算符必须被定义为类的成员函数，把这些运算符通过全局函数进行重载时会出现编译错误；
* 如果有一个操作数是类类型（如 string 类），那么对于对称操作符（比如操作符“==”），最好通过全局函数的方式进行重载。

### 运算符重载的限制

实现运算符重载时，需要注意以下几点：

* 重载后运算符的操作数至少有一个是用户定义的类型；
* 不能违反运算符原来的语法规则；
* 不能创建新的运算符；
* 有一些运算符是不能重载的，如“sizeof”；
* =、()、[]、-> 操作符只能被类的成员函数重载。

### operator=

某些情况下，当我们编写一个类的时候，并不需要为该类重载“=”运算符，因为编译系统为每个类提供了默认的赋值运算符“=”，使用这个默认的赋值运算符操作类对象时，该运算符会把这个类的所有数据成员都进行一次赋值操作。例如有如下类：

```cpp
class A
{
public:
    int a;
    int b;
    int c;
};
```

但是，在下面的示例中，使用编译系统提供的默认赋值运算符，就会出现问题了

```cpp
#include <iostream>
#include <string.h>
 
using namespace std;
 
class ClassA
{
public:
    ClassA()
    {
    
    }
 
    ClassA(const char* pszInputStr)
    {
        pszTestStr = new char[strlen(pszInputStr) + 1];
        strncpy(pszTestStr, pszInputStr, strlen(pszInputStr) + 1);
    }
    virtual ~ClassA()
    {
        delete pszTestStr;
    }
public:
    char* pszTestStr;
};
 
int main()
{
    ClassA obj1("liitdar");
 
    ClassA obj2;
    obj2 = obj1;
 
    cout << "obj2.pszTestStr is: " << obj2.pszTestStr << endl;
    cout << "addr(obj1.pszTestStr) is: " << &obj1.pszTestStr << endl;
    cout << "addr(obj2.pszTestStr) is: " << &obj2.pszTestStr << endl;
 
    return 0;
}
```

当对象 obj1 和 obj2 进行析构时，由于重复释放了同一块内存空间，导致程序崩溃报错。在这种情况下，就需要我们重载赋值运算符“=”了

我们修改一下前面出错的示例代码，编写一个包含赋值运算符重载函数的类，修改后的代码内容如下：

```cpp
#include <iostream>
#include <string.h>
 
using namespace std;
 
class ClassA
{
public:
    ClassA()
    {
    
    }
    ClassA(const char* pszInputStr)
    {
        pszTestStr = new char[strlen(pszInputStr) + 1];
        strncpy(pszTestStr, pszInputStr, strlen(pszInputStr) + 1);
    }
    virtual ~ClassA()
    {
        delete pszTestStr;
    }
    // 赋值运算符重载函数
    ClassA& operator=(const ClassA& cls)
    {
        // 避免自赋值
        if (this != &cls)
        {
            // 避免内存泄露
            if (pszTestStr != NULL)
            {
                delete pszTestStr;
                pszTestStr = NULL;
            }
 
            pszTestStr = new char[strlen(cls.pszTestStr) + 1];
            strncpy(pszTestStr, cls.pszTestStr, strlen(cls.pszTestStr) + 1);
        }
        
        return *this;
    }
    
public:
    char* pszTestStr;
};
 
int main()
{
    ClassA obj1("liitdar");
 
    ClassA obj2;
    obj2 = obj1;
 
    cout << "obj2.pszTestStr is: " << obj2.pszTestStr << endl;
    cout << "addr(obj1.pszTestStr) is: " << &obj1.pszTestStr << endl;
    cout << "addr(obj2.pszTestStr) is: " << &obj2.pszTestStr << endl;
 
    return 0;
}
```

## 拷贝构造函数

拷贝构造函数是一种特殊的构造函数，它在创建对象时，是使用同一类中之前创建的对象来初始化新创建的对象。拷贝构造函数通常用于：

* 通过使用另一个同类型的对象来初始化新创建的对象。
* 复制对象把它作为参数传递给函数。
* 复制对象，并从函数返回这个对象。

```cpp
#include <iostream>
 
using namespace std;
 
class Line
{
   public:
      int getLength( void );
      Line( int len );             // 简单的构造函数
      Line( const Line &obj);      // 拷贝构造函数
      ~Line();                     // 析构函数
 
   private:
      int *ptr;
};
 
// 成员函数定义，包括构造函数
Line::Line(int len)
{
    cout << "调用构造函数" << endl;
    // 为指针分配内存
    ptr = new int;
    *ptr = len;
}
 
Line::Line(const Line &obj)
{
    cout << "调用拷贝构造函数并为指针 ptr 分配内存" << endl;
    ptr = new int;
    *ptr = *obj.ptr; // 拷贝值
}
 
Line::~Line(void)
{
    cout << "释放内存" << endl;
    delete ptr;
}
int Line::getLength( void )
{
    return *ptr;
}
 
void display(Line obj)
{
   cout << "line 大小 : " << obj.getLength() <<endl;
}
 
// 程序的主函数
int main( )
{
   Line line1(10);
 
   Line line2 = line1; // 这里也调用了拷贝构造函数
 
   display(line1);
   display(line2);
 
   return 0;
}
```

当上面的代码被编译和执行时，它会产生下列结果：

```shell
调用构造函数
调用拷贝构造函数并为指针 ptr 分配内存
调用拷贝构造函数并为指针 ptr 分配内存
line 大小 : 10
释放内存
调用拷贝构造函数并为指针 ptr 分配内存
line 大小 : 10
释放内存
释放内存
释放内存
```

## 函数重载 overload

实现函数重载的条件：

* 同一个作用域
* 参数个数不同
* 参数类型不同
* 参数顺序不同

```cpp
//1. 函数重载条件
namespace A{
 void MyFunc(){ cout << "无参数!" << endl; }
 void MyFunc(int a){ cout << "a: " << a << endl; }
 void MyFunc(string b){ cout << "b: " << b << endl; }
 void MyFunc(int a, string b){ cout << "a: " << a << " b:" << b << endl;}
    void MyFunc(string b, int a){cout << "a: " << a << " b:" << b << endl;}
}

//2.返回值不作为函数重载依据
namespace B{
 void MyFunc(string b, int a){}
 //int MyFunc(string b, int a){} //无法重载仅按返回值区分的函数
}
```

注意: 函数重载和默认参数一起使用，需要额外注意二义性问题的产生。

```cpp
void MyFunc(string b){
 cout << "b: " << b << endl;
}

//函数重载碰上默认参数
void MyFunc(string b, int a = 10){
 cout << "a: " << a << " b:" << b << endl;
}

int main(){
 MyFunc("hello"); //这时，两个函数都能匹配调用，产生二义性
 return 0;
}
```

### 函数重载实现原理

编译器为了实现函数重载，也是默认为我们做了一些幕后的工作，编译器用不同的参数类型来修饰不同的函数名，比`void func();`编译器可能会将函数名修饰成`_func`，当编译器碰到`void func(int x)`,编译器可能将函数名修饰为`_func_int`,当编译器碰到`void func(int x,char c)`,编译器可能会将函数名修饰为`_func_int_char`我这里使用“可能”这个字眼是因为编译器如何修饰重载的函数名称并没有一个统一的标准，所以不同的编译器可能会产生不同的内部名

```cpp
void func(){}
void func(int x){}
void func(int x,char y){}
```

以上三个函数在linux下生成的编译之后的函数名为

```cpp
_Z4funcv //v 代表void,无参数
_Z4funci //i 代表参数为int类型
_Z4funcic //i 代表第一个参数为int类型，第二个参数为char类型
```

## 函数重写 overwrite

函数重写（overwrite）和函数重载（over load）是 C++ 中常见的用法。一般情况下，它们都被放在一起比较，本文重点只介绍函数重写，原因如下：

1. 函数重载的概念比较简单也容易理解；
2. 函数重载和函数重写放在一起容易混淆

函数重载其实就是复用了同一个函数名而已，重载的函数只是要求参数列表不同，可以是参数类型不同，参数个数不同，或参数顺序不同等。同上，重载也不能用返回值来区别。

**函数覆盖是子类和父类之间的关系，是垂直关系；而重载是同一个类中不同方法之间的关系，是水平关系**

代码 1

```cpp
class Entity {
public:
    Entity(){};
    void Func(int a)
    {
        std::cout << "Entity" << std::endl;
    }
};

class Person : public Entity {
public:
    Person() {};
    void Func(int a)
    {
        std::cout << "Person" << std::endl;
    }
};

int main()
{
    Entity* e = new Person();
    e->Func(0); // 输出 Entity
    std::cin.get();
}
```

Entity 类和 Person 类里面定义了两个一模一样的函数 Func，这两个类之间虽然是继承关系，但是这两个函数之间没有任何关系，它们只是属于不同类里面的方法。

代码 2

```cpp
#include <iostream>

class Entity {
public:
    Entity(){};
    virtual void Func(int a)
    {
        std::cout << "Entity" << std::endl;
    }
};

class Person : public Entity {
public:
    Person() {};
    void Func(int a)
    {
        std::cout << "Person" << std::endl;
    }
};

int main()
{
    Entity* e = new Person();
    e->Func(0); // 输出 Person
    std::cin.get();
}
```

Entity 类和 Person 类里面定义了两个一模一样的函数 Func，唯一不同的是，基类中的函数被关键字 virtual 修饰了，很明显，这是一个虚函数。当定义一个指向派生类的基类对象的指针时，调用该函数时，实际指向的是派生类中的函数。

代码 3

```cpp
#include <iostream>

class Entity {
public:
    Entity(){};
    void Func(int a)
    {
        std::cout << "Entity" << std::endl;
    }
};

class Person : public Entity {
public:
    Person() {};
    void Func(std::string a)
    {
        std::cout << "Person" << std::endl;
    }
};

int main()
{
    Entity* e = new Person();
    e->Func(0);  // 输出 Entity
    e->Func("0");  // 编译报错：不能调用派生类成员函数
    std::cin.get();
}
```

从函数签名的概念可知，基类 Entity 和派生类 Person 中分别定义了两个不同的函数，也就是说，这两个函数也毫无瓜葛，基类指针当然也就不能访问派生类中的函数了。

函数覆盖存在于父类和子类的关系中，实际上对应的就是虚函数的概念。

## 函数覆盖 override

如果派生类在虚函数声明时使用了override描述符，那么该函数必须重载其基类中的同名函数，否则代码将无法通过编译

C++ 11 中引入了 override 关键字以帮助防止在覆盖虚函数时出现的一些小问题。例如， 在下面的程序中就存在这样的错误。

```cpp
// This program has a subtle error in the virtual functions.
#include <iostream>
#include <memory>
using namespace std;

class Base
{
    public:
        virtual void functionA(int arg) const{cout << "This is Base::functionA" << endl; }
};

class Derived : public Base
{
    public:
        virtual void functionA(long arg) const{ cout << "This is Derived::functionA" << endl; }
};
int main()
{
    // Base pointer b points to a Derived class object.
    shared_ptr<Base>b = make_shared<Derived>();
    // Call virtual functionA through Base pointer.
    b->functionA(99);
    return 0;
}
```

程序输出结果：

```cpp
This is Base::functionA
```

在该程序中，Base 类指针 b 指向 Derived 类对象。因为 functionA 是一个虚函数，所以一般可以认为 b 对 functionA 的调用将选择 Derived 类的版本。

但是，从程序的输出结果来看，实际情况并非如此。其原因是这两个函数有不同的形参类型，所以 Derived 类中的 functionA 不能覆盖 Base 类中的 functionA。基类中的函数釆用的是 int 类型的参数，而派生类中的函数釆用的则是 long 类型的参数，因此，Derived 类中的 functionA 只不过是重载 Base 类中的 functionA 函数。

要确认派生类中的成员函数覆盖基类中的虚成员函数，可以在派生类的函数原型（如果函数以内联方式写入，则在函数头）后面加上 override 关键字。override 关键字告诉编译器，该函数应覆盖基类中的函数。如果该函数实际上没有覆盖任何函数，则会导致编译器错误。

下面的程序演示了上面程序的修改方法，使得 Derived 类的函数可以真正覆盖 Base 类的函数。请注意，在该程序中已经将 Derived 类函数的形参修改为 int，并且在函数头中添加了 override 关键字。

```cpp
//This program demonstrates the use of the override keyword.
#include <iostream>
#include <memory>
using namespace std;

class Base
{
    public:
        virtual void functionA(int arg) const { cout << "This is Base::functionA" << endl;}
};
class Derived : public Base
{
    public:
        virtual void functionA(int arg) const override{ cout << "This is Derived::functionA" << endl; }
};
int main()
{
    // Base pointer b points to a Derived class object.
    shared_ptr<Base>b = make_shared<Derived>();
    // Call virtual functionA through Base pointer.
    b->functionA(99);
    return 0;
}
```

程序输出结果：

```cpp
This is Derived::functionA
```

## 内联函数 inline

C++ 内联函数是通常与类一起使用。如果一个函数是内联的，那么在编译时，编译器会把该函数的代码副本放置在每个调用该函数的地方。

对内联函数进行任何修改，都需要重新编译函数的所有客户端，因为编译器需要重新更换一次所有的代码，否则将会继续使用旧的函数。

如果想把一个函数定义为内联函数，则需要在函数名前面放置关键字 inline，在调用函数之前需要对函数进行定义。

在类定义中的定义的函数都是内联函数，即使没有使用 inline 说明符。

下面是一个实例，使用内联函数来返回两个数中的最大值：

```cpp
#include <iostream>
 
using namespace std;

inline int Max(int x, int y)
{
   return (x > y)? x : y;
}

// 程序的主函数
int main( )
{

   cout << "Max (20,10): " << Max(20,10) << endl;
   cout << "Max (0,200): " << Max(0,200) << endl;
   cout << "Max (100,1010): " << Max(100,1010) << endl;
   return 0;
}
```

使用内联函数可以使程序更快，因为它们消除了与函数调用关联的开销。 编译器可以通过对普通函数不可用的方式来优化内联扩展的函数。

在使用内联函数时要留神：

1. 在内联函数内不允许使用循环语句和开关语句；
2. 内联函数的定义必须出现在内联函数第一次调用之前；
3. 类结构中所在的类说明内部定义的函数是内联函数。

# 数据类型

## 强制转换

### static_cast

基本等价于隐式转换的一种类型转换运算符，`static_cast`可用于需要明确隐式转换的地方。

可用于低风险的转换。

### const_cast

`const_cast`的对象类型必须为指针引用或指向对象的指针

通过`const_cast`运算符，也只能将`const type*`转换为`type*`，将`const type&`转换为`type&`

也就是说源类型和目标类型除了 const 属性不同，其他地方完全相同

#### 用法1

```cpp
int main()
{
	const int a = 1;
	int*b = const_cast<int*>(&a);
	*b = 5;
	std::cout << a;
}
```

断点查看运行到`*b = 5;`时，`a`的值被设置成5，但最后 cout 的值仍为1

对于 const 数据，我们要做这样的保证：决不能对 const 数据进行重新赋值

如果我们不想修改 const 变量的值，那我们又为什么要“去 const”呢？

原因是，我们可能调用了一个参数不是 const 的函数，而我们要传进去的实际参数却是 const 的，但是我们知道这个函数是不会对参数做修改的，于是我们就需要使用 const_static 去除 const 限定，以便函数能够接受这个实际参数

#### 用法2

常成员函数的 this 指针为 const xxx 型，即指向的地方的数据不能变，于是使用 const_cast

```cpp
class father
{public:
	virtual void func()const
	{
		const_cast<father*>(this)->aa = 1;
	}
	int aa;
};
```

### dynamic_cast

定义两个简单的类

```cpp
class father
{
};
class son:public father
{
public:
	int num;
};
```

将父类指针转换为子类指针

```cpp
int main()
{
  father f1;
  son s1;
  father* pfather=&f1;
  son* pson = &s1;
  // 错误 "father *"类型的值不能用于初始化"son *"类型的实体
  son* pson = pfather;
}
```

此时，`pson`虽然为子类指针，但他实际指向的是父类对象的空间，编译器认为可能通过该指针访问到此空间中不存在的部分，因此编译不能通过

因此使用 dynamic_cast 通过 RTTI（运行时类别识别）来做转换，而 RTTI 通过虚函数来实现，因此在父类里添加一个虚函数

```cpp
class father
{
	virtual void func() {};
};
```

此时再做转换，即使访问了不存在的对象在编译阶段将不会出错

```cpp
int main()
{
  father f1;
  son s1;
  father* pfather = &f1;
  son* pson = &s1;
  pson = dynamic_cast<son*>(pfather);
  // 错误
  pson->num = 1;
}
```

### reinterpret_cast

执行各种高风险转换，如整型转指针，各种类型的指针转换，父类子类指针的转换

```cpp
int i = 1;
int* a = reinterpret_cast<int*>i;
```

等价于 C 中的强制转换

```c
int i=1;
int*a=(int*)i;
```

# 语法

## switch case

如果在某一 case 中定义了变量，此变量是局部变量，作用域直到遇到下一个花括号才终结，如果此 case 中未使用 `{}`，会报错

```cpp
int main()
{
    int a =0;
    switch(a)
    {
        case 0: int b = 0;break;
        case 1: break;
        default:break;
    }
    return 0;
}
```

编译器提示错误：

```bash
testswitch.cpp: In function ‘int main()’:
testswitch.cpp:9: error: jump to case label
testswitch.cpp:8: error:   crosses initialization of ‘int b’
testswitch.cpp:10: error: jump to case label
testswitch.cpp:8: error:   crosses initialization of ‘int b’
```

出现这样的提示，你很有可能在某个case标记中定义了局部变量，而后面还有其他的case标记或者default语句。比如说这里的整形变量b。

看看编译器提示的信息 cross initialization of int b, 什么意思呢， 就是说跳过了变量的初始化，仔细想想，确实是这样，我们在case 0 中定义了变量b，在这个程序中，直到遇到switch的“｝”右花括号，b的作用域才终结，也就是说 在case 1 和 default 分支中 变量b依然是可以访问的。考虑这样一种情况，如果switch匹配了case 1，这样case 0的代码被跳过了，那么b就没有定义，如果此时在case 1的代码中访问了b，程序会崩溃的。如果谁也不匹配，执行default也会有同样的危险。

知道了错误的原因，解决起来就很简单了

1. 将case 0 标记 的代码用 `{}` 括起来，这样b的作用域在这个花括号内。在其他的case 标记中不能访问。
2. 将 变量b放在 switch外面 定义。

# 宏

## 取整

### 向下取整

Return the down number of aligned at specified width. `ALIGN_DOWN(13, 4)` would return 12.

`#define ALIGN_DOWN(size, align)  ((size) & ~((align) - 1))`

计算`size`以`align`为倍数的下界数

### 向上取整

Return the most contiguous size aligned at specified width. `ALIGN_UP(13, 4)` would return 16.

`ALIGN_UP(size, align)  (((size) + (align) - 1) & ~((align) - 1))`

计算`size`以`align`为倍数的上界数

注：`size`应当为2的 n 次方，即2, 4, 8, 16...

# 指针

## 指向数组的指针

在下面的声明中

```cpp
double a[50]
```

`a` 是一个指向 `&a[0]` 的指针，即数组 `a` 的第一个元素的地址。下面的程序片段把 `p` 赋值为 `a` 的第一个元素的地址

```cpp
double *p;
double a[10];

p = a;
```

使用数组名作为常量指针是合法的，反之亦然。因此，`*(a + 4)` 是一种访问 `a[4]` 数据的合法方式

### 参考链接

1. [Linux中_ALIGN宏背后的原理](https://blog.csdn.net/wangpeihuixyz/article/details/40593619)
2. [C 数据对齐算法](https://blog.csdn.net/sean_8180/article/details/84675716)
3. [LEARN C++](https://www.learncpp.com/)
4. [Google 开源项目风格指南](https://zh-google-styleguide.readthedocs.io/en/latest/)
