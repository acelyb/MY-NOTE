# 字符串驻留机制

## 说明

字符串驻留是一种仅保存一份相同且不可变字符串的方法。不同的值被存放在字符串驻留池中，发生驻留之后, 许多变量可能指向内存中的相同字符串对象, 从而节省内存

## 原理

* 系统维护interned字典，记录已被驻留的字符串对象
* 当字符串对象a需要驻留时，先在interned检测是否存在，若存在则指向存在的字符串对象，a的引用计数减1
* 若不存在，则记录a到interned中

## 驻留时机

**所有长度为 0 和长度为 1 的字符串都被驻留**

**字符串只在编译时进行驻留，而非运行时**

```python
a = 'hi' # a变量被驻留
b = ''.join(['h', 'i']) # 变量不会被驻留
print(a is b) # False
```

**字符串中只包含字母，数字或下划线时将会驻留**

```python
a = 'hello'
b = 'hello'
print(a is b) # True

a = 'hello!'
b = 'hello!'
print(a is b) # False
```

常量折叠是 Python 中的一种 窥孔优化技术. 这意味着在编译时表达式 `a*20` 会被替换为 `aaaaaaaaaaaaaaaaaaaa` 以减少运行时的时钟周期. 只有长度小于 20 的字符串才会发生常量折叠.样的设计目的是为了保护.pcy文件不会被错误代码搞的过大

```python
a = 'a' * 10
b = 'aaaaaaaaaa'
print(a is b) # True

a = 'a' * 21
b = 'aaaaaaaaaaaaaaaaaaaaa'
print(a is b) #False
```

优点：能够提高一些字符串处理任务在时间和空间上的性能，非驻留比较效率为o(n)，驻留时比较效率为o(1)

缺点：在创建或驻留字符串时的会花费更多的时间
