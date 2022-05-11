# CPP tips

## const 相关

### 函数名后加 const

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

### 常对象

常类型的对象必须进行初始化，而且不能被更新。

* 常引用：被引用的对象不能被更新。
const  类型说明符  &引用名
* 常对象：必须进行初始化,不能被更新。
类名  const  对象名
* 常数组：数组元素不能被更新。
类型说明符  const  数组名[大小]...
* 常指针：指向常量的指针。

## static 相关

### 静态成员函数

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

### 静态数据成员

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

## 函数相关

### 友元

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

### 调用规则

当同时存在直接基类和间接基类时，每个派生类只负责其直接基类的构造。

### 构造函数和析构函数的构造规则

#### 派生类可以不定义构造函数的情况

* 当具有下述情况之一时，派生类可以不定义构造函数。
* 基类没有定义任何构造函数。
* 基类具有缺省参数的构造函数。
* 基类具有无参构造函数。

#### 派生类必须定义构造函数的情况

* 当基类或成员对象所属类只含有带参数的构造函数时，即使派生类本身没有数据成员要初始化，它也必须定义构造函数，并以构造函数初始化列表的方式向基类和成员对象的构造函数传递参数，以实现基类子对象和成员对象的初始化。

#### 派生类的构造函数只负责直接基类的初始化

C++语言标准有一条规则：如果派生类的基类同时也是另外一个类的派生类，则每个派生类只负责它的直接基类的构造函数调用。

这条规则表明当派生类的直接基类只有带参数的构造函数，但没有默认构造函数时（包括缺省参数和无参构造函数），它必须在构造函数的初始化列表中调用其直接基类的构造函数，并向基类的构造函数传递参数，以实现派生类对象中的基类子对象的初始化。

这条规则有一个例外情况，当派生类存在虚基类时，所有虚基类都由最后的派生类负责初始化。

#### 总结

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
