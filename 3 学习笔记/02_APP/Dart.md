---
title: Dart 语言入门
aliases:
  - Dart 基础
  - Dart Basics
created: 2026-08-05
updated: 2026-08-05
series: Dart / Flutter 学习
part: 1
source: Dart 入门 + 进阶字幕（基础 009–040；进阶 001/003–004/007–015/018–021/024–026/029–032）+ dart.dev 官方文档（Dart 3.12）
tags:
  - type/literature-note
  - topic/dart
  - topic/flutter
  - status/draft
---

# Dart 语言入门

> [!summary]
> Dart 是面向对象语言：**一切皆对象**（含数字、函数、`null`）。本笔记按课程字幕整理基础类型、集合、流程控制、函数与异常，以及进阶的 **库/类/继承/Mixin/泛型/异步与文件 I/O**，并对照 [dart.dev](https://dart.dev/language) 补上 **Sound Null Safety**、`final`/`const`、现代 `switch`、`async`/`await` 等现行写法。学完可接 [[Flutter]]。

> [!warning] 课程与现行 Dart 的差异
> 字幕课程偏旧（约 Dart 1/2 时代）。现行默认启用 **Sound Null Safety**：
> - 非空类型（如 `bool`、`int`）**必须先初始化**，不能隐式为 `null`。
> - 允许为 `null` 时写成 `bool?`、`int?`、`String?`。
> - `new` 可选；`List()` 无参构造在 null-safe 下已禁用，优先用字面量 `[]`。
> - Dart 3 的 `switch` **非空 case 默认不穿透**，多数情况可不写 `break`。
> - `_` 私有是 **库（library）级**，不是 Java 式“仅本类可见”。
> - Mixin 现行优先用 `mixin` 声明；异步优先 `async`/`await`，少手写 `.then`。

官方入口：[Language tour](https://dart.dev/language) · [Classes](https://dart.dev/language/classes) · [Constructors](https://dart.dev/language/constructors) · [Mixins](https://dart.dev/language/mixins) · [Generics](https://dart.dev/language/generics) · [Asynchrony](https://dart.dev/libraries/async/async-await) · [dart:io](https://dart.dev/libraries/dart-io)

## 本章目录

| 章节 | 学什么 | 对应字幕 |
| --- | --- | --- |
| §1 核心概念 | 对象、变量、`var`、空安全 | 基础 009 |
| §2 内置类型 | `bool` / `num`/`int`/`double` / `String` | 009–011 |
| §3 final 与 const | 只赋值一次 vs 编译期常量 | 012 |
| §4 控制台 I/O | `dart:io`、`stdin`/`stdout`/`stderr` | 013 |
| §5 枚举与集合 | `enum`、`List`、`Set`、`Queue`、`Map` | 016–020 |
| §6 流程控制 | `assert`、`if`、作用域、`switch`、循环 | 023–028 |
| §7 函数 | 参数、一等公民、匿名函数 | 031–035 |
| §8 异常 | `Error`/`Exception`、`try`/`on`/`catch`/`finally`、`throw` | 038–040 |
| §9 库与导入 | `dart:` / `package:`、pub、版本约束 | 001, 003–004 |
| §10 类与成员 | 构造、`this`、私有、getter/setter、static | 007–015 |
| §11 继承体系 | `extends` / `with` / `implements` / `abstract` | 018–021 |
| §12 泛型 | 函数与类上的类型参数、约束 | 024–026 |
| §13 异步与文件 | Sync/Async、`Directory`/`File` | 029–032 |
| 文末速查 | 语法对照与易错点 | — |

---

## 1. 核心概念

程序入口是顶层 `main()`：

```dart
void main() {
  print('Hello, World!');
}
```

要点（官方 Important concepts）：

1. **一切皆对象**：能放进变量的都是对象；每个对象是某个类的实例。数字、函数、`null` 也是对象。
2. **强类型 + 类型推断**：可写 `var x = 1;`（推断为 `int`），也可显式注解。
3. **库级私有**：标识符以 `_` 开头时，对该 **library** 私有（没有 `public`/`private` 关键字）。
4. **Null Safety**：默认非空；可空类型加 `?`；确定非空可用 `!`（失败则抛异常）。

```dart
bool isOn = false;      // 非空，必须有值
bool? maybeOn;          // 可空，默认 null
var inferred = true;    // 推断为 bool
print(inferred.runtimeType); // bool
```

字符串插值：`$变量` 或 `${表达式}`。

```dart
print('isOn = $isOn');
print('type = ${isOn.runtimeType}');
```

---

## 2. 内置类型

### 2.1 bool

只有字面量 `true` / `false`（均为编译期常量）。条件与 `assert` **必须是真正的 bool**，不能写 `if (obj)` 这种“真值”判断。

```dart
var fullName = '';
assert(fullName.isEmpty);

var hitPoints = 0;
assert(hitPoints == 0);
```

### 2.2 数字：num / int / double

| 类型 | 含义 |
| --- | --- |
| `int` | 整数（无小数点） |
| `double` | 64 位浮点（IEEE 754） |
| `num` | `int` 与 `double` 的父类型，可交替持有两者 |

```dart
int age = 34;
double temperature = 20.5;
num either = 1;
either += 2.5; // OK

// 字符串 ↔ 数字
var one = int.parse('1');
var onePointOne = double.parse('1.1');
String s = 3.14159.toStringAsFixed(2); // '3.14'

// 解析失败时可给默认值（课程里的 onError；现行也可用 tryParse）
var safe = int.tryParse('abc') ?? 0;
```

算术与赋值：`+ - * /`、`++`/`--` 等。语句以分号 `;` 结束。

### 2.3 String

UTF-16 序列；单引号 / 双引号均可；三引号多行；`r'...'` 为 raw 字符串。

常用 API（课程演示）：

```dart
String name = 'Brian Kearns';

name.substring(0, 5);          // 'Brian'
var space = name.indexOf(' ');
name.substring(space).trim();  // 'Kearns'
name.length;
name.contains('ryan');         // 大小写敏感
var parts = name.split(' ');   // List：['Brian', 'Kearns']
```

相邻字符串字面量会自动拼接；也可用 `+`。

---

## 3. final 与 const

课程把“不可变”统称 const；官方区分更细：

| 关键字 | 含义 |
| --- | --- |
| `final` | **运行时**只赋值一次；之后不能改引用 |
| `const` | **编译期常量**；隐含 `final` |

```dart
final String hello = 'hello';
const String world = 'world';

// hello = 'hi';  // 错误：只能赋值一次
// world = 'name'; // 错误：常量不能再赋值
```

`const` 还可修饰 **值**（常量列表/Map 等）：

```dart
var foo = const [];
const baz = []; // 等价于 const []
```

> [!note]
> 课程报错文案里出现 “cannot assign to **final** variable”，正是因为 `const` 变量本质也是 final。

---

## 4. 控制台输入输出

控制台程序常用：

```dart
import 'dart:io';

void main() {
  stdout.write('What is your name?\r\n'); // 注意换行；print 会自动换行
  final name = stdin.readLineSync();

  if (name == null || name.isEmpty) {
    stderr.writeln('Name is empty');
  } else {
    print('Hello, $name');
  }
}
```

| API | 作用 |
| --- | --- |
| `stdout` | 标准输出（类似 `print`，但需自己处理换行） |
| `stdin.readLineSync()` | **同步**读一行，阻塞直到用户回车 |
| `stderr` | 标准错误（常用于错误提示） |

多数 Dart I/O 是异步的；`readLineSync` 是为了顺序交互准备的同步 API。Flutter UI 应用里很少直接用这些。

---

## 5. 枚举与集合

### 5.1 enum

枚举是一组**有限、固定**的实例。必须声明在顶层（不能塞进 `main` 函数体）。

```dart
enum Color { red, green, blue }

void main() {
  print(Color.values); // [Color.red, Color.green, Color.blue]
  print(Color.red);
}
```

Dart 3 还有 **enhanced enum**（可带字段、方法、构造函数），以及上下文明确时的 **dot shorthand**（如 `Color c = .red;`）。详见 [Enums](https://dart.dev/language/enums)。

### 5.2 List（有序、可重复、可按下标访问）

Dart **没有独立的 array 类型**；数组语义由 `List` 承担。下标从 **0** 开始。

```dart
var test = [1, 2, 3, 4];
print(test.length);      // 4
print(test[0]);          // 1
print(test.elementAt(3)); // 4

// 泛型约束元素类型
List<int> numbers = [];
numbers.add(1);
// numbers.add('cats'); // 分析错误：String 不是 int

// 未指定泛型时，元素可以是多种类型（实际是 List<Object?>/dynamic 相关）
var things = [];
things.add(1);
things.add('cats');
things.add(true);
```

优先用字面量；需要固定长度等再用命名构造（见官方 Collections）。

### 5.3 Set（无序、不重复）

```dart
var ids = <int>{};
ids.add(1);
ids.add(2);
ids.add(1); // 无效：已存在
print(ids); // {1, 2}
```

### 5.4 Queue（双端队列，需 `dart:collection`）

适合“排队”：从两端增删，**不按中间下标随机插入**。

```dart
import 'dart:collection';

void main() {
  var q = Queue<int>();
  q.addAll([1, 2, 3, 4]);
  q.removeFirst();
  q.removeLast();
  print(q); // (2, 3) 或等价表示
}
```

### 5.5 Map（键值对）

```dart
var people = {
  'dad': 'Brian',
  'son': 'Chris',
  'daughter': 'Heather',
};

print(people.keys);
print(people.values);
print(people['dad']); // Brian

var more = <String, String>{};
more.putIfAbsent('dad', () => 'Brian');
print(more['son']); // null（键不存在）
```

键唯一；用键取值，不必记索引。

---

## 6. 流程控制

### 6.1 assert

开发期断言：条件为 `false` 时抛出 `AssertionError`。

```dart
var age = 43;
assert(age == 43);
// assert(age == 15); // 失败

assert(
  age >= 0,
  'age should be non-negative',
);
```

生产环境通常关闭断言（Flutter debug 开启；`dart run` 可用 `--enable-asserts`）。

### 6.2 if / else

条件必须是 `bool`。花括号 `{}` 划定 **作用域（scope）**。

```dart
var age = 43;

if (age == 43) {
  print('You are 43');
} else if (age < 18) {
  print('Minor');
  if (age < 13) {
    print('Not even a teenager');
  }
} else if (age > 65) {
  print('Senior');
} else {
  print('Adult');
}
```

三元表达式：`condition ? expr1 : expr2`。

### 6.3 作用域（Scope）

变量“住”在声明它的那一层 `{}` 里；内层可见外层，外层不可见内层。

```dart
void main() {
  var age = 56;

  if (age > 18) {
    var hasBills = true;
    print('$age, hasBills=$hasBills');
  }

  // print(hasBills); // 错误：不在作用域内
}
```

函数参数、局部变量同理：同名变量可在不同作用域共存，互不干扰。

### 6.4 switch

适合**离散、具体**的值（常与 `enum` 搭配）；不适合 `case < 18` 这类区间（应用 `if`）。

**现代 Dart 3 写法**（非空 case 执行完默认结束，不必 `break`）：

```dart
var age = 18;

switch (age) {
  case 18:
    print('You can vote');
  case 21:
    print('Adult');
  case 65:
    print('Senior');
  default:
    print('Nothing special');
}
```

还可写 **switch 表达式**、pattern matching、`when` 守卫等（见 [Branches](https://dart.dev/language/branches)）。

> [!note]
> 旧课程强调每个 `case` 末尾写 `break` 以防穿透；Dart 3 默认不穿透。空 `case` 才会 fall-through。

### 6.5 循环

| 结构 | 特点 |
| --- | --- |
| `while` | **先判断**再执行；可能一次都不跑 |
| `do { } while` | **先执行**再判断；至少跑一次 |
| `for` | 初始化 / 条件 / 步进，不易写成无意死循环 |
| `for-in` / `forEach` | 遍历 `Iterable` |

```dart
var value = 1;
const max = 5;

do {
  print(value);
  value++;
} while (value < max);

value = 1;
while (value < max) {
  print(value);
  value++;
}

// 经典 for：需要下标时用
var people = ['Brian', 'Heather', 'Chris'];
for (var i = 0; i < people.length; i++) {
  print('${people[i]} at $i');
}

// for-in：不需要下标
for (final person in people) {
  print(person);
}

// forEach + tear-off / 匿名函数
people.forEach(print);
people.forEach((p) => print(p));
```

`break` 跳出循环；`continue` 进入下一轮。注意 `while (true)` 这类**死循环**，必须有明确退出条件。

---

## 7. 函数

函数也是对象，类型为 `Function`。推荐为公开 API 写清参数与返回类型。

### 7.1 基础

```dart
void sayHello(String name) {
  print('Hello, $name');
}

int dogYears(int age) => age * 7; // 箭头语法 = { return ...; }

int squareFeet(int width, int length) {
  return width * length;
}

void main() {
  sayHello('Brian');
  print(dogYears(43)); // 301
  print(squareFeet(10, 20));
}
```

`void` 表示不使用返回值。未写 `return` 时，函数隐式返回 `null`（返回类型非 `void` 时需注意空安全）。

### 7.2 可选位置参数 `[]`

必须放在参数列表**末尾**；未传时为 `null` 或你给的默认值（默认值须为编译期常量）。

```dart
void sayHello([String name = '']) {
  if (name.isNotEmpty) {
    name = name.padLeft(name.length + 1); // 前面加空格
  }
  print('Hello$name');
}

void download(String file, [bool open = false]) {
  print('Downloading $file');
  if (open) print('Opening $file');
}
```

### 7.3 命名参数 `{}`

调用时用 `name: value`，顺序无关。默认可选；需要必填时加 `required`。

```dart
int squareFeet({required int width, required int length}) {
  return width * length;
}

void download(String file, {int port = 80}) {
  print('Download $file on port $port');
}

void main() {
  print(squareFeet(length: 5, width: 10)); // 50
  download('myfile');           // port 80
  download('myfile2', port: 90);
}
```

> [!note]
> **同一函数**不能同时混用“可选位置参数 `[]`”和“命名参数 `{}`”（只能二选一，再加必选位置参数）。

### 7.4 函数作为对象（一等公民）

```dart
int calcYears(int age, int multiplier) => age * multiplier;

void main() {
  var dog = calcYears;
  var cat = calcYears;
  print(dog(43, 7));  // 301
  print(cat(43, 12)); // 516
}
```

传给 `forEach` 时优先 **tear-off**：`list.forEach(print);`，不必再包一层 `(x) => print(x)`。

### 7.5 匿名函数（lambda / closure）

```dart
const people = ['Brian', 'Heather', 'Chris'];

people.forEach((person) {
  print(person);
});

// where 过滤 → 新的 Iterable
people
    .where((name) => name != 'Brian')
    .forEach(print); // Heather, Chris
```

闭包可捕获词法作用域中的变量（见官方 Lexical closures）。

---

## 8. 异常与错误

### 8.1 Error vs Exception（概念）

| | 大致含义 |
| --- | --- |
| `Error` | 程序失败 / 不应轻易“吞掉”的严重问题（如断言失败、误用 API） |
| `Exception` | 预期内可恢复的异常情况 |

Dart **没有** Java 式 checked exception；可 `throw` 任意非 null 对象。未捕获时通常导致 isolate / 程序终止。

### 8.2 try / on / catch / finally

```dart
try {
  // 可能失败的代码
} on FormatException catch (e) {
  print('格式问题: $e');      // 指定类型用 on
} on Exception catch (e) {
  print('其他 Exception: $e');
} catch (e, s) {
  print('未知: $e\n$s');      // 捕获一切；第二个参数是 StackTrace
} finally {
  // 无论成败都执行：关文件、关连接等清理
}
```

课程示例：捕获 `NoSuchMethodError` 等具体类型；`finally` 保证清理逻辑总会跑。

部分处理后继续向上抛：用 `rethrow`。

### 8.3 throw

主动抛出更清晰的错误，便于调用方分支处理：

```dart
int dogYears(int? age) {
  if (age == null) {
    throw ArgumentError.notNull('age');
  }
  if (age < 0) {
    throw ArgumentError.value(age, 'age', 'must be >= 0');
  }
  // 也可自定义：throw Exception('dog years must use factor 7');
  return age * 7;
}

void main() {
  try {
    print(dogYears(null));
  } on ArgumentError catch (e) {
    print('参数错误: $e');
  } catch (e) {
    print('未知: $e');
  } finally {
    print('done');
  }
}
```

原则：不要静默吞掉错误；该失败就失败，并给出可读信息。

---

## 9. 库与导入

### 9.1 Dart 2 / 类型系统（课程背景）

Dart 2 起强化 **sound / type-safe** 类型系统：集合等要明确元素类型，避免 `List` 里混进 `int` 又混 `String` 却无人察觉。

```dart
// 明确类型
var list = <int>[];
list.add(1);
// list.add('x'); // 分析错误
```

包的 `pubspec.yaml` 应用 **SDK 上下界**（例：`sdk: '>=3.0.0 <4.0.0'`），避免跨大版本 silently 坏掉。跟旧视频对不上时：先看配套源码 / changelog，再查 [dart.dev](https://dart.dev)。

### 9.2 import 形态

| 前缀 | 含义 |
| --- | --- |
| `dart:...` | 语言自带库（`dart:core` 默认可用；另有 `dart:async`、`dart:math`、`dart:convert`、`dart:io`…） |
| `package:...` | pub 包或本项目 `lib/` 下代码 |
| 相对路径 | 同项目其它 `.dart` 文件 |

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'my_class.dart';
```

`as` 起前缀，避免名字冲突。还可用 `show` / `hide` 精简导出符号（见 [Libraries](https://dart.dev/language/libraries)）。

### 9.3 示例：`dart:convert`（编码 ≠ 加密）

```dart
import 'dart:convert';

void main() {
  const original = 'hello world';
  final bytes = utf8.encode(original);
  final encoded = base64Encode(bytes);
  final decoded = utf8.decode(base64Decode(encoded));
  print('$original → $encoded → $decoded');
}
```

Base64 是**编码**（换表示），不是加密。

### 9.4 示例：pub 包 `http`

1. 在 [pub.dev](https://pub.dev) 找包 → Installing 说明。
2. 写入 `pubspec.yaml` 的 `dependencies`，保存后 `pub get`。
3. 代码里 `import`，异步请求用 `await`（课程用 `.then`，现行更推荐下面写法）：

```dart
import 'package:http/http.dart' as http;

Future<void> main() async {
  final response = await http.get(Uri.parse('https://example.com'));
  print(response.statusCode); // 200 = OK
  print(response.body);
}
```

---

## 10. 类与成员

类是**蓝图**；用构造函数生成**实例**（对象）。Dart 有 GC，无显式析构函数。

### 10.1 定义与实例化

```dart
class Greeter {
  void sayHello(String name) => print('Hello, $name');
}

void main() {
  final mine = Greeter(); // new 可选
  final yours = Greeter();
  mine.sayHello('Brian');
  yours.sayHello('42');
}
```

### 10.2 构造函数与 `this`

默认无参构造一直存在，直到你自定义。参数与字段同名时用 `this.` 消歧；官方还支持 **初始化形参** 简写。

```dart
class Dog {
  int age;
  String name;

  // 推荐简写（初始化形参）
  Dog(this.age, this.name);

  // 等价于课程写法：
  // Dog(int age, String name) {
  //   this.age = age;
  //   this.name = name;
  // }
}

void main() {
  final bob = Dog(6, 'Bob');
  print('${bob.name} is ${bob.age * 7} in dog years');
}
```

还可命名构造、工厂构造、`const` 构造、转发到 `super`（见 [Constructors](https://dart.dev/language/constructors)）。子类**不继承**父类构造函数签名。

### 10.3 词法作用域再强调

`{}` 划定作用域；内层可看见外层。同名局部变量会**遮蔽**外层——构造参数、局部 `var`、字段三者撞名时最容易写错。原则：**不要复用易混的名字**；字段赋值写清 `this.field`。

### 10.4 公有 / 私有（封装）

标识符以 `_` 开头 → **对当前 library 私有**（同文件或 `part` 体系内可见；其它库不可见）。

```dart
class Animal {
  String _name;   // 库内私有
  int _age;
  String breed;   // “公有”字段

  Animal(this._name, this._age, this.breed);

  void describe() => print('$_name, $_age, $breed');

  void _meow() => print('Meow'); // 私有方法，外部库调不到

  void speak() => _meow();       // 类内可调
}
```

> [!note]
> 课程常说“类外不可见”；严格说是 **库外** 不可见。同一 `.dart` 文件里其它顶层代码仍能访问 `_` 成员。

### 10.5 Getter / Setter

实例字段默认已有隐式 getter；非 `final` 还有 setter。自定义可在读写时做校验或换算：

```dart
class Dog {
  String _name;
  int _age; // 存“狗岁”

  Dog(this._name, int humanYears) : _age = humanYears;

  String get name => _name;
  set name(String value) => _name = value;

  int get age => _age;
  set age(int humanYears) => _age = humanYears * 7;
}
```

对外仍像属性：`dog.age = 4;`，不必写成方法调用。

### 10.6 static（类级成员）

`static` 属于**类本身**，所有实例共享；**没有 `this`**，也不能通过实例去“拥有一份独立副本”。

```dart
class Animal {
  static int count = 0;
  Animal() {
    count++;
  }

  static void run() => print('running');
}

void main() {
  Animal();
  Animal();
  print(Animal.count); // 2
  Animal.run();        // 通过类名调用
}
```

仅在“全类一份 / 无需实例”时用 static（计数器、工具方法、常量等）。

---

## 11. 继承、Mixin、接口、抽象

### 11.1 单继承 `extends`

Dart **单继承**：一条 `extends` 链。子类获得父类成员；用 `super` 调父类实现；可用 `@override` 标注重写。

```dart
class Animal {
  void breathe() => print('breathing');
}

class Mammal extends Animal {
  bool warmBlooded = true;
  void test() => print('test in mammal');
}

class Feline extends Mammal {
  bool hasClaws = true;

  @override
  void test() {
    print('test in feline');
    super.test();
  }
}
```

### 11.2 Mixin：`with`（复用，不是真·多继承）

不能 `extends A, B`。用 `with` 混入额外能力。现行推荐显式 `mixin`：

```dart
mixin Dragon {
  void breatheFire() => print('🔥');
}

mixin Ghost {
  void walkThroughWalls() => print('👻');
}

class Monster extends Feline with Dragon, Ghost {
  void glow() => print('glows in the dark');
}
```

注意：多个 mixin / 父类若有同名成员，**靠 `with` 列表顺序**决定最终实现，容易踩坑。Mixin 有约束（不能声明某些构造等），详见 [Mixins](https://dart.dev/language/mixins)。

### 11.3 接口 `implements`

每个类都隐式定义接口。`implements` 表示**履约**：必须自行实现对方公开的实例成员；**不继承实现**，也没有“拿来即用的 `super.对方方法`”。

```dart
class Employee {
  String name = '';
  void test() => print('employee');
}

class Manager implements Employee {
  @override
  String name = 'Bob';

  @override
  void test() => print('manager');
}
```

| | `extends` | `implements` |
| --- | --- | --- |
| 拿到实现？ | 是 | 否，自己写 |
| `super` 调对方？ | 可以 | 不适用对方 API |
| 数量 | 只能一个父类 | 可实现多个 |

### 11.4 抽象类 `abstract`

抽象类描述“概念骨架”，**不能直接实例化**。可含：已实现成员 + 未实现（抽象）成员。子类 `extends` 后必须补齐抽象成员。

```dart
abstract class Car {
  int doors;
  Car(this.doors);

  void honk(); // 抽象：无方法体

  void describe() => print('doors=$doors'); // 可有具体实现
}

class RaceCar extends Car {
  RaceCar() : super(2);

  @override
  void honk() {
    print('beep beep');
    // 若父类 honk 已有实现，才可 super.honk()
  }
}
```

---

## 12. 泛型

泛型让**同一份代码**在保持类型安全的前提下处理多种类型。约定常用 `T`（Type）、`E`（Element）、`K`/`V`（Key/Value）。

### 12.1 泛型函数

```dart
// T 必须是 num 的子类型
T addNumbers<T extends num>(T a, T b) {
  // 注意：a + b 的静态类型是 num，常需再转换或换写法
  return (a + b) as T;
}

void main() {
  print(addNumbers(1, 2));     // int
  print(addNumbers(1.5, 2.5)); // double
}
```

课程示例：对 `List` 做累加时，元素类型由调用处推断；`T extends num` 保证能做算术。

### 12.2 泛型类

```dart
class Counter<T extends num> {
  final List<T> items = [];

  void add(T value) => items.add(value);

  num total() {
    num sum = 0;
    for (final v in items) {
      sum += v;
    }
    return sum;
  }
}

void main() {
  final c = Counter<int>();
  c.add(1);
  c.add(2);
  print(c.total()); // 3

  // Counter<int> 不能 add(1.5)；若要混用 int/double，用 Counter<num>
}
```

`List<E>`、`Map<K,V>`、`Set<E>` 本身就是泛型集合。

---

## 13. 同步 / 异步与文件 I/O

### 13.1 Sync vs Async

| | 同步（`...Sync`） | 异步（`Future` / `async`） |
| --- | --- | --- |
| 行为 | 当前调用卡住，直到完成 | 不堵死事件循环，完成后回调/`await` |
| 类比 | 单窗口排队 | 多窗口同时办事 |
| 适用 | 简单脚本、启动时一次性工作 | UI、网络、大量 I/O（Flutter 几乎总用异步） |

课程为降低难度多用 `existsSync`、`listSync` 等；写 Flutter 时应优先异步 API + `async`/`await`。

### 13.2 临时目录

```dart
import 'dart:io';

void main() {
  final dir = Directory.systemTemp.createTempSync('myapp_');
  print(dir.path);

  if (dir.existsSync()) {
    dir.deleteSync(recursive: true);
  }
}
```

`Directory.systemTemp` 指向系统临时区；`createTempSync` 每次生成新目录，进程结束后未必立刻删，系统会择机清理。

### 13.3 列举目录项

```dart
import 'dart:io';

void main() {
  final dir = Directory('.');
  final entities = dir.listSync(recursive: true, followLinks: false);

  for (final entity in entities) {
    final stat = entity.statSync();
    print('${entity.path}  type=${stat.type}  size=${stat.size}');
  }
}
```

`listSync` 可选 `recursive`、`followLinks`。条目是 `FileSystemEntity`（文件 / 目录 / 链接），`statSync()` 给出大小、权限、时间等。

### 13.4 读写文件

```dart
import 'dart:io';

void writeFile(String path, {FileMode mode = FileMode.write}) {
  final file = File(path);
  final raf = file.openSync(mode: mode); // append 追加；write 覆盖
  raf.writeStringSync('hello\r\nhow are you today?\r\n');
  raf.flushSync(); // close 通常也会 flush；大缓冲时显式 flush 更稳妥
  raf.closeSync();
}

void readFile(String path) {
  final file = File(path);
  if (!file.existsSync()) {
    stderr.writeln('file not found');
    return;
  }
  print(file.readAsStringSync());
  final bytes = file.readAsBytesSync();
  bytes.forEach(print);
}

void main() {
  writeFile('myfile.txt', mode: FileMode.append);
  readFile('myfile.txt');
}
```

| 模式 | 效果 |
| --- | --- |
| `FileMode.write` | 覆写（从空内容开始写） |
| `FileMode.append` | 在末尾追加 |

也有整文件便捷 API：`writeAsStringSync` / `readAsStringSync`；异步对应去掉 `Sync` 并 `await`。

---

## 文末速查

### 类型与变量

```dart
var x = 1;                 // 推断
final y = 'once';          // 只赋值一次
const z = 42;              // 编译期常量
int? n;                    // 可空，默认 null
late String description;   // 延迟初始化非空变量
```

### 集合字面量

```dart
var list = <int>[1, 2];
var set  = <String>{'a', 'b'};
var map  = <String, int>{'a': 1};
```

### 函数参数形态

| 写法 | 调用 |
| --- | --- |
| `f(int a, int b)` | `f(1, 2)` 位置必选 |
| `f(int a, [int b = 0])` | `f(1)` / `f(1, 2)` |
| `f({required int a, int b = 0})` | `f(a: 1)` / `f(b: 2, a: 1)` |

### 易错点

1. 课程里未初始化的 `bool`/`int` 打印 `null` → 现行要用 `bool?` / `int?`。
2. `List` 越界 → `RangeError`。
3. `int` 不能赋 `double`；需要两边都能装时用 `num`。
4. `Set` 自动去重；`Map` 缺键取值得 `null`（注意空安全下的类型）。
5. `Queue` 记得 `import 'dart:collection';`。
6. 死循环：`while (true)` / `do { } while (true)` 必须有 `break` 条件。
7. 旧课程的 `switch`+`break` → Dart 3 多数情况可不写 `break`。
8. `_` 是 **库级私有**，不是“仅本类”。
9. `implements` 不继承实现；别对接口父类型写 `super.对方方法`。
10. Mixin 同名成员看 `with` 顺序；冲突时只生效一套。
11. `FileMode.write` 会冲掉旧内容；要保留历史用 `append`。
12. Flutter / UI 里避免在主 isolate 狂用 `...Sync` I/O。

### OOP 速记

```dart
class A {}
class B extends A {}                    // 单继承
mixin M { void m() {} }
class C extends B with M {}             // Mixin
class D implements A { /* 自己实现 */ }
abstract class E { void f(); }          // 不可直接 new
```

### 建议阅读顺序（官方）

1. [Language tour](https://dart.dev/language)
2. [Null safety](https://dart.dev/null-safety)
3. [Classes](https://dart.dev/language/classes) / [Mixins](https://dart.dev/language/mixins) / [Generics](https://dart.dev/language/generics)
4. [Effective Dart](https://dart.dev/effective-dart)
5. [Async](https://dart.dev/libraries/async/async-await) → [[Flutter]] Widget / `Future` / `Stream`

---

## 相关笔记

- [[Flutter]]
- 源材料：`临时文件/`  
  - 基础：Booleans → Throwing Exceptions  
  - 进阶：Dart2 / Imports / Classes → Abstraction / Generics / Sync·File I/O

## 待处理

- [x] 补齐 `001` 版本变化、`003`/`004` Imports
- [x] 类 / 构造函数 / 继承 / Mixin / 接口 / 抽象
- [x] 泛型与 `dart:io` 文件基础（同步向）
- [ ] 深入：`factory` / 命名构造 / `const` 构造 / extension methods
- [ ] 异步进阶：`Future`、`Stream`、`async*`（Flutter 高频）
- [ ] Isolates / 并发模型（可选）
