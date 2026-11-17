---
title: Cocos Creator 入门
aliases:
  - Cocos
  - Cocos Creator 项目结构
  - Cocos 文件格式
  - 见缝插针
created: 2026-11-17
updated: 2026-11-17
source: Cocos Creator 3.8 官方手册（项目结构）+ CK《见缝插针》教程字幕（P04–P05，已校正 ASR）
tags:
  - type/literature-note
  - topic/cocos
  - topic/game-dev
  - status/draft
---

# Cocos Creator 入门

> [!summary]
> 先认工程长什么样：你只在 `assets/` 里创作，其余多为编辑器/构建产物。资源靠同名 `.meta` 的 UUID 被引用，改名或移动请在编辑器里做。实战以 **见缝插针**（Creator 3.8 + TS）串起来：改 Camera 背景 → 摆圆 → `angle` 旋转 → 再做插针。本文以 **Cocos Creator 3.x（文档参考 3.8）** 为准。

## 本章目录

| 章节 | 学什么 | 对应课程 |
| --- | --- | --- |
| §1 项目目录与文件格式 | 顶层目录、`assets` 常用后缀、`.meta`、版本控制 | 手册 |
| §2 背景色与圆圈 | 预览布局、Camera Clear Color / Clear Flags、Sprite 贴素材 | P04 |
| §3 旋转圆圈 | 挂脚本、`@property` 速度、`update` 改 `node.angle`、子节点观察旋转 | P05 |
| （后续） | 创建针、插针逻辑、构建发布… | — |

---

## 1. 项目目录与文件格式

通过 Dashboard 新建并打开项目后，根目录大致如下：

```text
MyGame/
├── assets/          # 唯一源资源目录（你主要改这里）
├── settings/        # 项目设置（可进版本库）
├── extensions/      # 项目级扩展插件（按需）
├── profiles/        # 编辑器 / 构建相关配置
├── local/           # 本机布局、窗口等个人配置
├── library/         # 资源导入后的中间库（可删重建）
├── temp/            # 临时文件（可删重建）
├── build/           # 构建产物（构建后才有）
├── package.json     # 项目合法性标识之一
├── tsconfig.json    # TypeScript 配置（常见）
└── .gitignore
```

**合法性标志**：文件夹里必须同时有 `assets/` 和 `package.json`，才能被当作 Cocos Creator 项目打开。

**一条总规则**：只在 `assets/` 里放游戏内容；`library` / `temp` / `build` / `local` 当产物看待，不要手改当源码维护。

### 1.1 顶层目录说明

| 路径 | 作用 | 要不要进 Git |
| --- | --- | --- |
| `assets/` | 场景、预制体、脚本、贴图、音频、第三方库等；只有这里的内容会出现在资源管理器 | **要**（含每个资源旁的 `.meta`） |
| `settings/` | 「项目设置」面板的序列化结果（设计分辨率、物理、引擎模块等） | **要**（团队同步设置） |
| `extensions/` | 本项目自定义编辑器扩展；可手动建目录安装，删对应子文件夹即卸载 | **要**（若项目依赖扩展） |
| `package.json` | 项目元信息；与 `assets` 一起校验是否为合法工程 | **要** |
| `tsconfig.json` | TS 编译配置，常 `extends` 到 `temp/` 下生成文件 | **建议要** |
| `profiles/` | 编辑器配置、各平台构建配置、场景相关配置等 | 一般 **不要**（偏本机/个人） |
| `local/` | 面板布局、窗口大小与位置等本机信息 | **不要** |
| `library/` | `assets` 导入后的中间形态，体量大；丢了删掉再开工程会重建 | **不要** |
| `temp/` | 编辑器临时缓存；关掉编辑器后可手动删 | **不要** |
| `build/` | 「项目 → 构建发布」后按平台生成的可分发工程 | **不要**（重新构建覆盖） |

> [!tip]
> `library` 坏了或版本升级后异常：关掉编辑器 → 删整个 `library/` → 再打开项目，让它重新导入。不要往里塞自己的源文件。

设计源文件（如 Photoshop `.psd`、TexturePacker `.tps`）可以放在 `assets` **外面**单独管理，不必进资源管理器。

### 1.2 `assets/` 里常见文件格式

每个资源文件旁都会有一个**同名** `.meta`（例如 `player.png` ↔ `player.png.meta`）。引用靠 `.meta` 里的 UUID，不靠磁盘路径——所以路径变了只要 `.meta` 跟着走，场景/预制体里的引用不会断。

推荐按类型分子目录（名字可自定）：

```text
assets/
├── scenes/
│   ├── main.scene
│   └── main.scene.meta
├── prefabs/
│   ├── coin.prefab
│   └── coin.prefab.meta
├── scripts/
│   ├── PlayerControl.ts
│   └── PlayerControl.ts.meta
├── textures/
│   ├── player.png
│   └── player.png.meta
└── audio/
    ├── jump.mp3
    └── jump.mp3.meta
```

| 扩展名 | 类型 | 说明 |
| --- | --- | --- |
| `.scene` | 场景 | 节点树 + 组件属性的序列化；应用运行入口通常从一个场景开始 |
| `.prefab` | 预制体 | 可复用的节点树模板，结构与场景类似，根类型为预制体 |
| `.ts` / `.js` | 脚本 | 挂到节点上的组件逻辑；3.x 推荐 TypeScript |
| `.png` / `.jpg` / `.webp` … | 纹理 / 图片 | 可在导入设置里指定 SpriteFrame、压缩、是否打图集等 |
| `.mp3` / `.ogg` / `.wav` … | 音频 | 导入时可设是否预加载等 |
| `.json` | JSON 资源 | 配置表、数据等，运行时按资源加载 |
| `.anim` / `.animation` 等 | 动画相关 | 剪辑、状态机等（以编辑器实际类型为准） |
| `.mtl` / 材质资源 | 材质 | 渲染外观；具体后缀随资源类型变化 |
| `.meta` | 元数据 | UUID、importer、导入参数、子资源（`subMetas`）等 |

> [!warning] `.meta` 三条铁律
> 1. **不要手写 / 乱改 UUID**（由编辑器分配）。
> 2. **不要在系统资源管理器里直接改名或挪资源**（容易让文件与 `.meta` 对不上）；在 Cocos 资源管理器里操作。
> 3. **`.meta` 必须随资源一起进版本库**；只交资源、漏交 `.meta`，别人打开工程引用会全乱。

`.meta` 示意（字段由编辑器生成，勿手写当源码）：

```json
{
  "ver": "1.0.0",
  "uuid": "a1b2c3d4-0000-4000-8000-000000000001",
  "importer": "image",
  "type": "sprite-frame",
  "subMetas": {}
}
```

`.scene` / `.prefab` 本质是编辑器序列化的对象图（`__type__`、`__id__` 互相引用），**用编辑器改**，不要当普通 JSON 手写维护。顶层示意：

```json
{
  "__type__": "cc.Scene",
  "_name": "main",
  "_children": [{ "__id__": 2 }],
  "_globals": { "__id__": 10 }
}
```

### 1.3 `settings/`（项目设置）

3.x 常见结构是按「包」拆成多个 JSON，例如：

```text
settings/
└── v2/
    └── packages/
        ├── project.json   # 设计分辨率、分组、物理、渲染等
        ├── builder.json   # 构建相关选项
        └── engine.json    # 引擎模块裁剪等
```

改设置优先走编辑器 **项目设置** 面板，让它回写；直接改 JSON 容易写出当前版本不认的字段组合。

### 1.4 版本控制该交什么

官方建议：提交 `assets`、`extensions`、`settings`、`package.json`，以及你手动加入且工程依赖的文件（常见还有 `tsconfig.json`）。

| 提交 | 不提交 |
| --- | --- |
| `assets/`（**含全部 `.meta`**） | `library/` |
| `settings/` | `temp/` |
| `extensions/`（若有） | `build/` |
| `package.json`、`tsconfig.json` | `local/`、`profiles/`（常见做法） |
| `.gitignore` | 本机 IDE / 缓存杂项 |

新建工程时编辑器会生成 `.gitignore`，一般已排除上述产物目录。

> [!note]
> 协作时最常见的坑：一人在资源管理器外改名、或漏提交 `.meta` → 另一人打开场景引用丢失。约定：**资源操作只在编辑器里做；提交前检查 `.meta` 是否跟文件成对出现。**

---

## 2. 背景色与圆圈（见缝插针 · P04）

> [!summary]
> 2D 场景里游戏画面来自 **Camera 拍 Canvas**。背景色 = Camera 的 **Clear Color**（须配合 **Clear Flags = Solid Color**）。圆圈用 **Sprite** 节点挂 `Circle` 贴图即可。

### 2.1 预览与布局

1. 运行预览选 **编辑器内预览**（不必先上真机/浏览器）。
2. 点一下预览区的自适应缩放，让画面贴合窗口。
3. 把周围面板往外拽，中间场景视图留大一点；底部面板也可下拉，方便摆节点。

改完布局再 **重新运行**，方便对照真实效果。

### 2.2 为什么默认背景是黑的？

2D 场景结构可以记成：

```text
场景 → Canvas（画布上摆 UI / 2D 对象）
     → Camera（每帧拍摄画布 → 得到游戏画面）
```

Camera 每帧会先按 **Clear Flags** 处理上一帧，再画本帧内容。

| 属性 | 作用 |
| --- | --- |
| **Clear Flags** | 是否、以及如何清空上一帧 |
| **Clear Color** | 用颜色清空时，涂上去的那一层底色 |

默认 Clear Color 偏黑，所以一打开预览背景是黑的。课上改成略带黄/偏深的暖色底，再运行确认。

### 2.3 Clear Flags：Solid Color vs Don’t Clear

| Clear Flags | Clear Color 是否生效 | 表现（课上演示） |
| --- | --- | --- |
| **Solid Color** | 生效 | 每帧先涂成单一底色，再画本帧 → 正常背景、无「删不掉的残影」 |
| **Don’t Clear** | **无效** | 不清空上一帧；删掉节点后，屏幕上旧画面可能还在，直到有新内容覆盖或触发刷新 |

课上操作要点：

1. 选中 Camera → Clear Flags 先试 **Don’t Clear**，此时改 Clear Color **没用**。
2. 在 Camera 下临时建 **Label**（或 Sprite）移动/删除：移动时未必像 Unity 那样拖出「运动残影」；但 **删除后** 屏幕上往往还留着旧像素——因为本帧没有东西去盖住上一帧。
3. 实战游戏背景：Clear Flags 设回 **Solid Color**，再用 Clear Color 控底色。

> [!tip]
> 日常 2D 玩法几乎都用 **Solid Color**。Don’t Clear 只作理解用；残影/拖影若要做特效，通常另有后处理或自定义渲染，不必在入门阶段深究。

### 2.4 添加目标圆圈（Sprite）

素材包里至少两个图：**Circle**（圆）、**Pin**（针）。本节只用 Circle。

| 步骤 | 操作 |
| --- | --- |
| 1 | 层级里右键 → 创建 2D 对象 → **Sprite** |
| 2 | 节点改名为 `Circle` |
| 3 | Sprite 组件的 SpriteFrame 选素材 **Circle** |
| 4 | 颜色调成偏灰黑（不必纯黑，和暖色背景对比即可） |
| 5 | 放到画面偏上；中间以后留给分数，下方留给插针 |
| 6 | Content Size 可试 **300×300**（按针的粗细、两侧留白自行微调） |

布局预期（后续课会补）：

```text
        [ 旋转的 Circle ]
           （中间分数）
              ↑ 针从下方插入
```

> [!note]
> 圆的尺寸要给两侧留间距，否则针插上去会显得挤；具体数值以你素材比例为准，课上 300 只是参考。

---

## 3. 旋转圆圈（见缝插针 · P05）

> [!summary]
> 绕自身转 = 每帧改节点的 **`angle`（度）**。速度做成 `@property`，在 `update` 里用 `± rotateSpeed * deltaTime`；方向不对就改加减号。纯色圆看不出转时，在边上加个子 Sprite 当标记。

### 3.1 挂脚本

1. 选中 `Circle` 节点 → 右键 / 添加组件 → **自定义脚本**，命名 `Circle`（生成 `Circle.ts`）。
2. 把脚本组件挂到该节点上（拖脚本到属性检查器，或创建时已挂上）。
3. 双击用 **VS Code** 打开（编辑器默认外部脚本 IDE）。

围绕自身旋转，改的是节点上的 **`angle`**（2D 角度，单位：度），不是去转贴图像素本身。

### 3.2 速度属性 + `update` 改 `angle`

课上思路：每秒转多少度 → 乘 `deltaTime` 累加/累减到 `angle`。

```ts
import { _decorator, Component } from 'cc';
const { ccclass, property } = _decorator;

@ccclass('Circle')
export class Circle extends Component {
    /** 旋转速度：度 / 秒 */
    @property
    rotateSpeed = 90;

    update(deltaTime: number) {
        // 顺时针：减；逆时针：加（课上先加发现倒着转，再改成减）
        this.node.angle -= this.rotateSpeed * deltaTime;
    }
}
```

| 要点 | 说明 |
| --- | --- |
| `@property` | 暴露到属性检查器，运行前可调速度，不必改代码重编译思路 |
| `rotateSpeed = 90` | 默认每秒 90°，可在检查器里改快慢 |
| `deltaTime` | 上一帧到本帧的秒数；`速度 × Δt` 保证帧率不稳时角速度仍均匀 |
| `node.angle` | 2D 节点朝向；`+=` / `-=` 决定逆时针 / 顺时针 |

> [!tip] 方向先随便写
> 很多「正负方向」不必先验推：先给一个速度跑起来，转反了就把 `+=` 改成 `-=`（或给 `rotateSpeed` 填负数）。

### 3.3 看不出在转？加边缘标记

纯灰黑的圆旋转时几乎没有视觉变化。课上做法：

1. 在 `Circle` **下**再创建一个 **Sprite** 子节点。
2. SpriteFrame 随便选一个能辨认的小图（内置小圆点、绿点等均可）。
3. 把子节点摆到圆的 **边缘**。

父节点一转，子节点跟着转，就能看见角速度。这和后面「针插到圆上成为子节点、跟着转」是同一套父子变换。

```text
Circle          ← 挂 Circle.ts，每帧改 angle
└── Marker      ← 边缘小 Sprite，仅用于观察（或以后换成真针）
```

下节（字幕预告）：**创建针（Pin）**。

---
