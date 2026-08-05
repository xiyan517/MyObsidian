---
title: Flutter 入门
aliases:
  - Flutter 基础
  - Flutter Widgets
created: 2026-08-05
updated: 2026-08-05
series: Dart / Flutter 学习
part: 2
source: Flutter 入门字幕（003–007 环境；010–040 控件与布局）+ 练习代码（临时文件 main*.dart）+ docs.flutter.dev
tags:
  - type/literature-note
  - topic/flutter
  - topic/dart
  - status/draft
---

# Flutter 入门

> [!summary]
> Flutter 用 **Dart** 写 UI：一切界面都是 **Widget**。本笔记按课程字幕整理环境搭建、`MaterialApp`/`Scaffold`、状态与常用控件、布局与列表，并用练习代码补齐 **loading/错误态、ListTile、DrawerHeader、styleFrom、Image.network** 等落地写法。前置：[[Dart]]。

> [!warning] 课程与现行 Flutter 的差异
> 字幕偏旧（RaisedButton / FlatButton 时代）。现行默认 **Material 3** + Null Safety：
> | 旧 API | 现行 |
> | --- | --- |
> | `RaisedButton` | `ElevatedButton` |
> | `FlatButton` | `TextButton` |
> | `OutlineButton` | `OutlinedButton` |
> | `BottomNavigationBarItem(title: …)` | 用 `label:` |
> | `showDialog(child: …)` | 用 `builder:` |
> | `_scaffoldKey…showSnackBar` | 优先 `ScaffoldMessenger.of(context).showSnackBar` |
> | `new` | 可省略 |
> IDE：课程用 IntelliJ；现在也常用 **Android Studio / VS Code + Flutter 插件**。官网已迁至 [flutter.dev](https://flutter.dev)（旧 flutter.io）。

官方：[Get started](https://docs.flutter.dev/get-started) · [Widget catalog](https://docs.flutter.dev/ui/widgets) · [Layout](https://docs.flutter.dev/ui/layout) · [Buttons migration](https://docs.flutter.dev/release/breaking-changes/buttons)

## 本章目录

| 章节 | 学什么 | 对应字幕 |
| --- | --- | --- |
| §1 环境 | Android Studio / IDE / `flutter doctor` | 003–005 |
| §2 第一个应用 | `runApp`、`MaterialApp`、有无状态、热重载 | 006–007 |
| §3 状态与按钮 | `setState`、Elevated / Text / Icon | 010–013 |
| §4 输入与选择 | TextField、Checkbox、Radio、Switch、Slider、日期 | 016–021 |
| §5 Scaffold 结构 | AppBar、FAB、Drawer、Footer、底栏 | 024–028 |
| §6 反馈与对话框 | BottomSheet、SnackBar、Alert / Simple Dialog | 031–034 |
| §7 布局与列表 | Row/Column、Expanded、Card、图片、ListView | 037–040 |
| §8 练习代码对照 | 骨架 / Scaffold 综合 / 表单布局 / 国家列表 | `main*.dart` |
| 文末速查 | 骨架、易错点、阅读顺序 | — |

---

## 1. 环境搭建

### 1.1 Android 工具链

1. 安装 [Android Studio](https://developer.android.com/studio)。
2. **SDK Manager**：装若干 API（不必只追最新；课程时代常用 5.1–8，现在选较新稳定版即可）。
3. **AVD Manager**：创建模拟器（如 Pixel / Nexus），先完整开机再跑 Flutter。

### 1.2 IDE + Flutter 插件

- IntelliJ / Android Studio：Plugins → 搜 **Flutter**（会带上 Dart）→ 安装并重启。
- 也可 VS Code + Flutter 扩展。

### 1.3 Flutter SDK 与 Doctor

按 [Install](https://docs.flutter.dev/get-started/install) 装 SDK，终端执行：

```bash
flutter doctor
```

核对：Flutter、Android toolchain、IDE 插件等。`No devices` 在未开模拟器/真机时正常；开 AVD 或 USB 调试后再查。

> [!note]
> 跟旧视频对不上时：查配套源码 / changelog；`pubspec.yaml` 给 SDK 上下界（见 [[Dart]] §9）。

---

## 2. 第一个应用

### 2.1 创建与运行

IDE → New Flutter Project → 选 SDK 路径 → Run（先启动模拟器）。

核心入口：

```dart
import 'package:flutter/material.dart';

void main() {
  runApp(const MyApp());
}
```

`runApp` 把根 Widget 挂到屏幕上。

### 2.2 Stateless vs Stateful

| | 含义 |
| --- | --- |
| `StatelessWidget` | 无内部可变状态；属性来自构造参数 |
| `StatefulWidget` | 有可变状态；真正状态在对应的 `State` 子类里 |

类比（课程）：人是 Widget，衣服是 State——换装改的是状态，不是“换一个人”。

计数器模板：`MyApp`（常 Stateless）→ `home: MyHomePage`（Stateful）→ `_MyHomePageState` 里 `_counter` + `setState`。

### 2.3 Hot Reload

保存后 **热重载**：UI 就地更新，多数状态保留。不生效时再 **Hot Restart** / 全量重启。

### 2.4 最小骨架（Scaffold）

两种常见挂法（练习代码两种都见过）：

```dart
// A. MaterialApp 写在 main 里（练习代码常用）
void main() {
  runApp(const MaterialApp(home: MyApp()));
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});
  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.blue,
        title: const Text('新的标题'),
      ),
      body: Container(
        padding: const EdgeInsets.all(20),
        child: const Center(
          child: Column(
            children: [
              Text('这是一个文本'),
              Text('这是第二个文本'),
            ],
          ),
        ),
      ),
    );
  }
}
```

```dart
// B. 根 Widget 自己返回 MaterialApp（计数器模板常见）
void main() => runApp(const MyApp());
// MyApp.build → return MaterialApp(home: Scaffold(...));
```

要点：

- `MaterialApp`：Material 风格应用壳（主题、路由等）。
- `Scaffold`：页面脚手架（AppBar / body / FAB / Drawer…）。
- `build` ≈ **渲染**；`BuildContext` 是树中位置与主题/导航的“上下文”。
- 单子用 `child`，多子用 `children`（`Column`/`Row`/`ListView`…）。
- `Container` + `padding` 是给 body 留白的常用套路。

课程用 Live Template 把骨架缩成缩写；可在 IDE Live Templates 里自建。

---

## 3. 状态与按钮

### 3.1 setState

在 **State 类**里改字段必须包进 `setState`，Flutter 才知道要重建 `build`：

```dart
String _value = 'Hello World';

void _onPressed() {
  setState(() {
    _value = 'My name is Brian';
  });
}
```

`onPressed: null` → 按钮禁用（常显灰）。

### 3.2 按钮（现行命名）

```dart
ElevatedButton( // 旧 RaisedButton：有阴影/抬起感
  onPressed: _onPressed,
  child: const Text('Click me'),
)

TextButton( // 旧 FlatButton：偏扁平，适合对话框操作
  onPressed: () {
    setState(() => _value = DateTime.now().toString());
  },
  child: const Text('Now'),
)

IconButton(
  icon: const Icon(Icons.add),
  onPressed: () => setState(() => _count++),
)
IconButton(
  icon: const Icon(Icons.remove),
  onPressed: () => setState(() => _count--),
)
```

### 3.3 onPressed 传“函数对象”

`onPressed` 要的是 `void Function()?`。若写成 `onPressed: _hello()`（带括号）会**立刻执行并传入返回值**（常为 `void`，报错）。应传引用：

```dart
void _hello(String msg) {
  setState(() => _value = msg);
}

ElevatedButton(
  onPressed: () => _hello('hi'), // 或定义无参包装函数再传入
  child: const Text('Say'),
)
```

（Dart 里函数也是对象，见 [[Dart]] §7。）

---

## 4. 输入与选择控件

### 4.1 TextField

模拟器需开启硬件键盘（AVD → Show Advanced → Enable Keyboard）才方便真机式输入。

```dart
String _change = '';
String _submit = '';

TextField(
  decoration: const InputDecoration(
    labelText: 'Hello',
    hintText: 'hint',
    icon: Icon(Icons.person),
  ),
  autocorrect: true,
  autofocus: true,
  keyboardType: TextInputType.number, // email / datetime / multiline…
  onChanged: (v) => setState(() => _change = v),
  onSubmitted: (v) => setState(() => _submit = v),
)
```

更稳妥：用 `TextEditingController` 读 `.text`（见 §7.2）；记得在 `State.dispose` 里 `controller.dispose()`。

### 4.2 Checkbox / Switch

成对出现：**裸控件** + **ListTile 版**（更大点击区、可带 title/subtitle）。

```dart
bool _v1 = false;
bool _v2 = false;

Checkbox(
  value: _v1,
  onChanged: (v) => setState(() => _v1 = v ?? false),
)

CheckboxListTile(
  value: _v2,
  onChanged: (v) => setState(() => _v2 = v ?? false),
  title: const Text('Hello'),
  subtitle: const Text('subtitle'),
  secondary: const Icon(Icons.info),
  controlAffinity: ListTileControlAffinity.leading,
  activeColor: Colors.green,
)
```

`Switch` / `SwitchListTile` API 几乎同构（开/关二态）。

### 4.3 Radio

同组互斥靠 **`groupValue`**；选项自己的 `value` 与之比较。

```dart
int? _group = 0;

Widget _radios() {
  final list = <Widget>[];
  for (var i = 0; i < 3; i++) {
    list.add(
      Radio<int>(
        value: i,
        groupValue: _group,
        onChanged: (v) => setState(() => _group = v),
      ),
    );
  }
  return Column(children: list);
}

// 或 RadioListTile：value / groupValue / onChanged + title…
```

### 4.4 Slider

```dart
double _value = 0;

Text('The value is ${(_value * 100).round()}')
Slider(
  value: _value,
  onChanged: (v) => setState(() => _value = v),
)
```

展示百分比时常 `* 100` 再 `round()`，避免一长串小数。

### 4.5 日期选择（异步）

```dart
String _date = '';

Future<void> _selectDate() async {
  final picked = await showDatePicker(
    context: context,
    initialDate: DateTime.now(),
    firstDate: DateTime(2016),
    lastDate: DateTime(2030),
  );
  if (picked != null) {
    setState(() => _date = picked.toString());
  }
}
```

`Future` + `async`/`await`：弹窗关闭前挂起，选完再继续（见 [[Dart]] 异步）。

---

## 5. Scaffold 结构件

`build` 返回的 `Scaffold` 是页面骨架；下列插槽都是可选。

### 5.1 AppBar

```dart
int _value = 0;

void _increment() => setState(() => _value++);
void _reset() => setState(() => _value = 0);

appBar: AppBar(
  backgroundColor: Colors.blue,
  title: const Text('新的标题'),
  actions: [
    IconButton(icon: const Icon(Icons.add), onPressed: _increment),
    IconButton(icon: const Icon(Icons.clear), onPressed: _reset),
  ],
)
```

`actions` 是 `List<Widget>`；右侧图标按钮常用来改同一页的状态（body 里用 `Text('值: $_value')` 显示）。

### 5.2 FloatingActionButton

```dart
String _dateTimeValue = '';

void _getDateTime() => setState(() {
  _dateTimeValue = DateTime.now().toString();
});

floatingActionButton: FloatingActionButton(
  onPressed: _getDateTime,
  backgroundColor: Colors.blue,
  mini: true,                 // 小号 FAB
  tooltip: '获取当前时间',     // 长按提示
  child: const Icon(Icons.access_time),
)
```

### 5.3 Drawer

默认从左侧滑出。更常见的是 **`DrawerHeader` + `ListTile`**，而不是裸 `Column` + 一个按钮：

```dart
drawer: Drawer(
  child: ListView(
    padding: EdgeInsets.zero,
    children: [
      const DrawerHeader(
        decoration: BoxDecoration(color: Colors.blue),
        child: Text(
          '菜单栏',
          style: TextStyle(color: Colors.white, fontSize: 24),
        ),
      ),
      const ListTile(
        leading: Icon(Icons.message),
        title: Text('消息'),
      ),
      const ListTile(
        leading: Icon(Icons.account_circle),
        title: Text('个人资料'),
      ),
      const ListTile(
        leading: Icon(Icons.settings),
        title: Text('设置'),
      ),
      BackButton(onPressed: () => Navigator.pop(context)), // 关闭抽屉
    ],
  ),
)
```

Drawer 与当前页共享同一 `State`。`Navigator.pop` 关掉抽屉；菜单项里再 `push` 其它页是进阶导航。

### 5.4 persistentFooterButtons

贴在屏幕底部；可把点击结果写回状态：

```dart
String _footerText = '';

void _updateFooterText(String text) {
  setState(() => _footerText = text);
}

persistentFooterButtons: [
  IconButton(
    icon: const Icon(Icons.timer_sharp),
    onPressed: () => _updateFooterText('计时器按钮被点击'),
  ),
  IconButton(
    icon: const Icon(Icons.alarm),
    onPressed: () => _updateFooterText('闹钟按钮被点击'),
  ),
]
```

### 5.5 BottomNavigationBar

在 `initState` 准备 items；`onTap` 里 `setState` 更新 `currentIndex`。

```dart
late List<BottomNavigationBarItem> _items;
int _index = 0;

@override
void initState() {
  super.initState();
  _items = const [
    BottomNavigationBarItem(icon: Icon(Icons.people), label: 'People'),
    BottomNavigationBarItem(icon: Icon(Icons.weekend), label: 'Weekend'),
    BottomNavigationBarItem(icon: Icon(Icons.message), label: 'Message'),
  ];
}

bottomNavigationBar: BottomNavigationBar(
  items: _items,
  currentIndex: _index,
  fixedColor: Colors.blue,
  onTap: (i) => setState(() => _index = i),
)
```

> [!note]
> `initState`：首帧 `build` **之前**初始化状态；不要在这里做超重同步工作（或配合异步 + loading）。

---

## 6. 反馈与对话框

### 6.1 Modal Bottom Sheet

自底部升起；**modal** = 必须先处理它，背后界面暂不可点。

```dart
void _showBottom() {
  showModalBottomSheet(
    context: context,
    builder: (BuildContext context) {
      return Container(
        height: 200,
        color: Colors.blue,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              '确认操作',
              style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('关闭'),
            ),
          ],
        ),
      );
    },
  );
}
```

`builder`：把“如何构建子树”交给框架，需要时才创建。

### 6.2 SnackBar

短时底部提示。现行推荐 `ScaffoldMessenger`（练习代码里即便留了 `GlobalKey<ScaffoldState>`，展示也走 Messenger）：

```dart
void _showSnackBar() {
  ScaffoldMessenger.of(context).showSnackBar(
    const SnackBar(
      content: Text('Hello World'),
      duration: Duration(seconds: 2),
    ),
  );
}
```

### 6.3 AlertDialog

```dart
Future<void> _showAlertDialog(String message) async {
  return showDialog(
    context: context,
    builder: (BuildContext context) {
      return AlertDialog(
        title: const Text('提示'),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('确定'),
          ),
        ],
      );
    },
  );
}
```

`title` / `content` 分开更清晰；操作按钮常用 **TextButton**。

### 6.4 SimpleDialog（带返回值）

```dart
enum Answers { yes, no, maybe }

String _askUserValue = '';

void _setValue(String valueStr) => setState(() => _askUserValue = valueStr);

Future<void> _askUser() async {
  final result = await showDialog<Answers>(
    context: context,
    builder: (context) => SimpleDialog(
      title: const Text('简单对话框'),
      children: [
        SimpleDialogOption(
          onPressed: () => Navigator.pop(context, Answers.yes),
          child: const Text('Yes'),
        ),
        SimpleDialogOption(
          onPressed: () => Navigator.pop(context, Answers.no),
          child: const Text('No'),
        ),
        SimpleDialogOption(
          onPressed: () => Navigator.pop(context, Answers.maybe),
          child: const Text('Maybe'),
        ),
      ],
    ),
  );

  switch (result) {
    case Answers.yes:
      _setValue('用户选择了 Yes');
    case Answers.no:
      _setValue('用户选择了 No');
    case Answers.maybe:
      _setValue('用户选择了 Maybe');
    case null: // 点遮罩 / 系统返回 = 取消
      _setValue('用户取消了');
  }
}
```

流程：`await showDialog` → `Navigator.pop(context, value)` → `switch`；**必须处理 `null`（取消）**。

---

## 7. 布局与列表

### 7.1 Row / Column

- `Column`：竖排；`Row`：横排；都用 `children`。
- `mainAxisAlignment` 控制主轴对齐。

登录表单常见结构：外层 `Column`，每行 `Row(标签, 输入框)`，下方按钮。

### 7.2 Expanded + TextEditingController（登录表单）

Row 里直接放 `TextField` 常报：

> Box constraints forces an infinite width

用 `Expanded` 吃掉剩余宽度。`controller` 读 `.text`，不必处处 `onChanged`：

```dart
final _user = TextEditingController();
final _password = TextEditingController();

@override
void dispose() {
  _user.dispose();
  _password.dispose(); // Controller 用完要释放
  super.dispose();
}

// body:
Column(
  children: [
    const Text('请填写内容登录'),
    Row(
      children: [
        const Text('用户名：'),
        Expanded(
          child: TextField(
            controller: _user,
            decoration: const InputDecoration(
              labelText: '用户名',
              hintText: '请输入用户名',
              prefixIcon: Icon(Icons.person),
            ),
          ),
        ),
      ],
    ),
    Row(
      children: [
        const Text('密码：'),
        Expanded(
          child: TextField(
            controller: _password,
            obscureText: true,
            decoration: const InputDecoration(
              labelText: '密码',
              hintText: '请输入密码',
              prefixIcon: Icon(Icons.lock),
            ),
          ),
        ),
      ],
    ),
    // 也可以不用 Row，整行 TextField（同一 controller 会同步内容）
    Padding(
      padding: const EdgeInsets.only(top: 20),
      child: Row(
        children: [
          Expanded(
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue,
                foregroundColor: Colors.white,
              ),
              onPressed: () {
                debugPrint('用户名：${_user.text}');
                debugPrint('密码：${_password.text}');
              },
              child: const Text('登录'),
            ),
          ),
        ],
      ),
    ),
  ],
)
```

> [!note]
> `ElevatedButton.styleFrom` 是现行改按钮颜色的常规写法（别再用旧的 `color:` 参数）。

### 7.3 Card + ListTile

```dart
Card(
  child: Container(
    padding: const EdgeInsets.all(20),
    child: const Column(
      children: [
        Text('卡片标题'),
        Text('卡片内容'),
      ],
    ),
  ),
)

Card(
  child: Column(
    children: const [
      ListTile(
        leading: Icon(Icons.album),
        title: Text('标题'),
        subtitle: Text('副标题'),
      ),
      Divider(),
      ListTile(
        leading: Icon(Icons.album),
        title: Text('标题'),
        subtitle: Text('副标题'),
      ),
    ],
  ),
)
```

`ListTile` = 左图标 + 标题/副标题的标准列表行；`Divider` 分隔。

### 7.4 图片：asset / network + BoxFit

1. 本地图放到如 `images/chapter-07.webp`，并在 `pubspec.yaml` 声明：

```yaml
flutter:
  assets:
    - images/chapter-07.webp
```

2. 使用（`fit` 控制裁剪/缩放）：

```dart
Expanded(
  child: Image.asset(
    'images/chapter-07.webp',
    fit: BoxFit.cover,
  ),
)
Expanded(
  child: Image.network(
    'https://flutter.github.io/assets-for-api-docs/assets/widgets/owl.jpg',
    fit: BoxFit.cover,
  ),
)
```

还有 `Image.file` / `Image.memory`。多图在 `Column` 里抢高度时靠 `Expanded`；改 assets 后需 **完全重启**。

### 7.5 ListView.builder + 网络 JSON（含 loading / 错误）

适合长列表：按需构建。完整状态应至少有三态：加载中 / 失败 / 成功。

```dart
Map<String, String> _countries = {};
bool _isLoading = false;
String? _error;

Future<void> getCountries() async {
  setState(() {
    _isLoading = true;
    _error = null;
  });

  try {
    final response = await http.get(
      Uri.parse('https://country.io/names.json'), // { "US": "United States", ... }
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      setState(() {
        _countries = data.map(
          (key, value) => MapEntry(key, value.toString()),
        );
      });
    } else {
      setState(() => _error = '请求失败: HTTP ${response.statusCode}');
    }
  } catch (e) {
    setState(() => _error = '请求失败: $e');
  } finally {
    setState(() => _isLoading = false);
  }
}

@override
void initState() {
  super.initState();
  getCountries(); // 不要放在 build 里
}

// body:
Column(
  children: [
    const Text('国家列表'),
    Expanded(
      child: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : ListView.builder(
                  itemCount: _countries.length,
                  itemBuilder: (context, index) {
                    final key = _countries.keys.elementAt(index);
                    return ListTile(
                      leading: Text(key),
                      title: Text(_countries[key] ?? ''),
                    );
                  },
                ),
    ),
  ],
)
```

依赖：`http`、`dart:convert`。行 UI 优先 `ListTile`，比手写 `Row` + 两个 `Text` 更规范。

> [!warning]
> **禁止**在 `build` 里发网络请求。`try/catch/finally` + `_isLoading` / `_error` 是最小可用错误处理。

---

## 8. 练习代码对照

临时文件里的四份 `main*.dart` 可当作本章活样板：

| 文件 | 练什么 | 对应章节 |
| --- | --- | --- |
| `main copy.dart` | 最小 `Scaffold`：AppBar + padding + Column 文本 | §2.4 |
| `main copy 3.dart` | Scaffold 全家桶：actions / FAB / Drawer / Footer / 底栏 / BottomSheet / SnackBar / Alert / SimpleDialog | §5–§6 |
| `main copy 4.dart` | 表单布局：`TextEditingController`、`Expanded`、`styleFrom`、`Card`+`ListTile`、`Image.asset`/`network` | §7.2–§7.4 |
| `main.dart` | 异步列表：`initState` 拉 JSON、loading/错误、`ListView.builder`+`ListTile` | §7.5 |

阅读建议：先跑 `main copy.dart` 确认工程，再打开 `main copy 3.dart` 点一遍各入口，最后对照 `main.dart` 看三态列表。

### 应用骨架

```dart
void main() => runApp(const App());

class App extends StatelessWidget {
  const App({super.key});
  @override
  Widget build(BuildContext context) {
    return const MaterialApp(home: Home());
  }
}

class Home extends StatefulWidget {
  const Home({super.key});
  @override
  State<Home> createState() => _HomeState();
}

class _HomeState extends State<Home> {
  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Title')),
        body: const Placeholder(),
      );
}
```

### 控件对照（课程 → 现行）

| 用途 | 现行 Widget |
| --- | --- |
| 实心按钮 | `ElevatedButton` / `FilledButton` |
| 文字按钮 | `TextButton` |
| 图标按钮 | `IconButton` |
| 输入 | `TextField` + `InputDecoration` / `Controller` |
| 多选 | `Checkbox` / `CheckboxListTile` |
| 单选 | `Radio` / `RadioListTile` |
| 开关 | `Switch` / `SwitchListTile` |
| 滑条 | `Slider` |
| 日期 | `showDatePicker` |
| 底栏导航 | `BottomNavigationBar` |
| 轻提示 | `SnackBar` via `ScaffoldMessenger` |
| 列表行 | `ListTile`（可放进 `Card` / `ListView`） |
| 列表 | `ListView.builder` |
| 加载中 | `CircularProgressIndicator` |
| 按钮样式 | `ElevatedButton.styleFrom(...)` |

### 易错点

1. 改 State 忘了 `setState` → UI 不更新。
2. `onPressed: fn()` 多写了括号。
3. Row 里裸 `TextField` / 无边界的贪心子组件 → 用 `Expanded`/`Flexible`。
4. 改 `assets` 只热重载不够 → 全量重启。
5. 网络请求写在 `build` → 放到 `initState`；并补 `_isLoading` / `_error`。
6. 旧按钮类已弃用 → 换 Elevated/Text/Outlined；颜色用 `styleFrom`。
7. 模拟器输不了字 → 开 Enable Keyboard。
8. `TextEditingController` 忘记 `dispose()` → 泄漏。
9. `showDialog` 返回 `null` 未处理 → 取消时逻辑落空。
10. SnackBar 继续用旧 `ScaffoldState.showSnackBar` → 改用 `ScaffoldMessenger`。

### 建议阅读顺序

1. 巩固 [[Dart]]（尤其函数、异步、集合）
2. 跑通 §8 四份练习代码
3. [Flutter get started](https://docs.flutter.dev/get-started)
4. [Layout tutorial](https://docs.flutter.dev/ui/layout/tutorial)
5. 导航 `Navigator` / `go_router` → 状态管理

---

## 相关笔记

- [[Dart]]
- 源材料：`临时文件/` Flutter 字幕 + `main*.dart` 练习代码

## 待处理

- [ ] 导航栈：`Navigator.push` / 命名路由 / `go_router`
- [ ] 主题与 Material 3（`ThemeData`、`ColorScheme`）
- [ ] 状态管理专题与表单校验（`Form` / `GlobalKey<FormState>`）
- [ ] `FutureBuilder` / `StreamBuilder` 替代手写 loading 三态（可选）
- [ ] 平台渠道 / 发布到应用商店（可选）
