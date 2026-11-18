---
title: Cocos Creator 入门
aliases:
  - Cocos
  - Cocos Creator 项目结构
  - Cocos 文件格式
  - 见缝插针
created: 2026-11-17
updated: 2026-11-17
source: Cocos Creator 3.8 官方手册（项目结构 / 2D 物理）+ 《见缝插针》教程字幕（P04–P11、P13–P15，已校正 ASR；P12 字幕暂缺）
tags:
  - type/literature-note
  - topic/cocos
  - topic/game-dev
  - status/draft
---

# Cocos Creator 入门

> [!summary]
> 先认工程长什么样：你只在 `assets/` 里创作，其余多为编辑器/构建产物。资源靠同名 `.meta` 的 UUID 被引用，改名或移动请在编辑器里做。实战以 **见缝插针**（Creator 3.8 + TS）串起来：改 Camera 背景 → 摆圆 → `angle` 旋转 → Pin Prefab → 三定位点 → 生成/tween/插入/跟转 → 分数 → **针头 Collider2D + RigidBody2D 碰撞** → **`gameOver`**。本文以 **Cocos Creator 3.x（文档参考 3.8）** 为准。

## 本章目录

| 章节 | 学什么 | 对应课程 |
| --- | --- | --- |
| §1 项目目录与文件格式 | 顶层目录、`assets` 常用后缀、`.meta`、版本控制 | 手册 |
| §2 背景色与圆圈 | 预览布局、Camera Clear Color / Clear Flags、Sprite 贴素材 | P04 |
| §3 旋转圆圈 | 挂脚本、`@property` 速度、`update` 改 `node.angle`、子节点观察旋转 | P05 |
| §4 针的 Prefab | 空节点 + 针身/针头子节点、缩放旋转配色、拖成预制体 | P06 |
| §5 针的三个定位点 | 生命周期、Position1/2/3、到位判定 vs 碰撞、挂到 Circle 跟随旋转 | P07 |
| §6 针的生成 | `GameManager`、`instantiate`、挂到管理器下、对齐 `p1` | P08 |
| §7 tween 控制针运动 | `Pin.moveTo`、`tween().to().start()`、生成后移到 `p2` | P09 |
| §8 控制针的插入 | `input` 触摸、`currentPin`、点击移到 `p3` 再刷新针 | P10 |
| §9 针跟随圆旋转 | tween `.call`、可选 `parentNode`、保世界坐标/旋转再换父 | P11 |
| §10 分数与 UI | `Label`、`score++`、`updateScore`、单例供 Pin 到位回调 | P13 |
| §11 针头碰撞检测 | `CircleCollider2D`、**`RigidBody2D`**、`BEGIN_CONTACT` | P14 |
| §12 游戏结束逻辑 | `isGameOver`、停转、禁止再发射；结束动画下节 | P15 |
| （后续） | 游戏结束动画（放大、改背景色）… | — |

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

| 路径              | 作用                                     | 要不要进 Git               |
| --------------- | -------------------------------------- | ---------------------- |
| `assets/`       | 场景、预制体、脚本、贴图、音频、第三方库等；只有这里的内容会出现在资源管理器 | **要**（含每个资源旁的 `.meta`） |
| `settings/`     | 「项目设置」面板的序列化结果（设计分辨率、物理、引擎模块等）         | **要**（团队同步设置）          |
| `extensions/`   | 本项目自定义编辑器扩展；可手动建目录安装，删对应子文件夹即卸载        | **要**（若项目依赖扩展）         |
| `package.json`  | 项目元信息；与 `assets` 一起校验是否为合法工程           | **要**                  |
| `tsconfig.json` | TS 编译配置，常 `extends` 到 `temp/` 下生成文件    | **建议要**                |
| `profiles/`     | 编辑器配置、各平台构建配置、场景相关配置等                  | 一般 **不要**（偏本机/个人）      |
| `local/`        | 面板布局、窗口大小与位置等本机信息                      | **不要**                 |
| `library/`      | `assets` 导入后的中间形态，体量大；丢了删掉再开工程会重建      | **不要**                 |
| `temp/`         | 编辑器临时缓存；关掉编辑器后可手动删                     | **不要**                 |
| `build/`        | 「项目 → 构建发布」后按平台生成的可分发工程                | **不要**（重新构建覆盖）         |

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

---

## 4. 创建针的 Prefab（见缝插针 · P06）

> [!summary]
> 针要反复生成 → 做成 **Prefab**。结构用空节点 `Pin` 当根，显示放在子节点：`PinBody`（针身）+ `PinHat`（针头圆）。调好缩放、朝向、颜色后拖进 `prefabs/`。

### 4.1 为什么用空节点当根？

显示（Sprite）放在 **子节点**，根节点 `Pin` 只负责整体位置/旋转/以后挂逻辑。这样改针身长度、针头大小不会把「整根针」的锚点逻辑搅乱；后续代码实例化、插到圆上，也只挪根节点即可。

### 4.2 搭层级

| 步骤 | 操作 |
| --- | --- |
| 1 | 创建 **空节点**，命名 `Pin`；可先放到画面偏下，方便和上方圆对比 |
| 2 | 把 Texture 里的 **Pin** 图拖到 `Pin` 下，改名为 `PinBody`（针身） |
| 3 | 再拖一份 **Circle** 到 `Pin` 下当针头，命名 `PinHead`（P07 定名；若曾用 `PinHat` 请改名后 **Apply** Prefab） |

目标层级：

```text
Pin                 ← 空节点（之后做成 Prefab 的根）
├── PinBody         ← 针身 Sprite（素材 Pin）
└── PinHead         ← 针头 Sprite（素材 Circle）
```

### 4.3 针身：长短、朝向、颜色

课上素材默认偏小、朝向也不对（针要从 **下往上** 插）。

| 调整 | 做法（课上参考） |
| --- | --- |
| 拉长 | 调 `PinBody` 的 **Scale**（可先拉大再微调到整数，如 **20**） |
| 加粗 | 用另一轴 Scale（课上用 **Y** 加宽） |
| 朝上 | `PinBody` 的 **angle = 90°**（按你素材默认朝向可能要 ±90，以预览为准） |
| 颜色 | 调成与圆接近的灰黑 |
| 出屏 | 和旋转圆对比；针放在下方待命时，别长到伸出屏幕 |

> [!tip]
> 先 Scale 出大致比例 → 运行预览 → 再改成整数。20 太长就略减；以「够插到圆、两侧不挤、不顶出屏」为准。

### 4.4 针头：大小、位置、统一配色

| 调整 | 做法（课上参考） |
| --- | --- |
| 尺寸 | Content Size 先试 30×30，偏大再改 **20×20** |
| 位置 | 拖到针身 **下方**（柄端/可见圆头那一端，按你旋转后的朝向对齐） |
| 颜色 | 与 `PinBody` 一致：在颜色字段上 **Ctrl+C / Ctrl+V** 复制粘贴 |

想整局配色统一，也可从大圆 `Circle` 复制同色到针身/针头。

### 4.5 做成 Prefab

1. 在 `assets` 下建（或使用）`prefabs/` 文件夹。
2. 把层级里的 `Pin` **拖进** `prefabs/`，生成 `Pin.prefab`。
3. 场景里若留下蓝色/预制体实例，可按需要保留作预览，或删掉实例只留资源——正式玩法里针应由代码 **实例化**。
4. Prefab 内改名（如 `PinHead`）后记得点 **Apply**，把修改写回资源。

| 概念 | 说明 |
| --- | --- |
| Prefab | 可复用的节点树模板（见 §1 `.prefab`） |
| 为何必须做 | 针会在场景里 **多次出现**，运行时不断 `instantiate`，不能每根手摆 |
| 改 Prefab | 改资源后，已有实例可同步；以后插针逻辑挂在根或单独脚本上即可 |

---

## 5. 针的三个定位点（见缝插针 · P07）

> [!summary]
> 针不直接蹦在屏内：先在屏外生成 → 移到待命点 → 点击再插到圆上。用三个空节点 `Position1/2/3` 只存坐标；「是否插上」课上用 **是否到达三号位** 判定，不必先上碰撞体。插上后把针设为 `Circle` 子节点即可跟着转。

### 5.1 一根针的生命周期

```text
屏外生成 (①)
    → 移入屏内待命 (②)
    → 玩家点击
    → 向上插到圆上 (③)
    → 与已插针的针头做碰撞/重叠判定 → 成功或失败
```

| 阶段 | 为何这样 |
| --- | --- |
| 先屏外再移入 | 直接在屏内刷出针会显得突兀，滑入更自然 |
| 点击才插入 | ② 是「就位、等操作」；点左键后才从 ② 冲向 ③ |
| 插上后跟圆转 | 把针设为 `Circle` 的 **子节点**，父转子跟转（同 §3.3） |
| 胜负 | 插入时跟 **其他已插针的针头** 是否碰撞/重叠（后续课实现） |

### 5.2 两种「插到圆上」的判定

| 方式 | 做法 | 课上选择 |
| --- | --- | --- |
| 碰撞 | 针与大圆都加 **BoxCollider**，碰撞回调里认为插上 | 可做，本课不用 |
| **到位** | 针运动到固定的 **三号位** 即视为已插上 | **采用**：路径是直线，终点已知，够用 |

> [!note]
> 三号位要摆在「针尖刚好没入圆」的视觉位置。后续代码只需判断是否到达该坐标（或 tween 完成），再 `setParent(Circle)`。

### 5.3 三个 Position 空节点

| 节点 | 含义 | 摆放提示 |
| --- | --- | --- |
| **Position1** | 生成点（一号位） | 屏外偏下；针从这里刷出 |
| **Position2** | 就位/待命（二号位） | 屏内下方；与 ① 留一点距离，移入才有「滑进来」的时间 |
| **Position3** | 插上圆的终点（三号位） | 再往上，对齐大圆边缘该插住的位置 |

它们 **只负责定位**，不挂玩法逻辑。

搭建步骤（课上）：

1. 建空节点 `Position1`；把预览用的 `Pin` 放它下面，**本地坐标归零**，再整体挪 `Position1` 到屏外——方便看见「生成点上的针长什么样」。
2. **Ctrl+D** 复制 → 改名为 `Position2`，上移到屏内待命处；若与 ① 太近就再把 ② 略下移。
3. 再 **Ctrl+D** → `Position3`，继续上移到插圆位置。
4. 正式跑流程时：实例化针到 ① 的世界坐标 → 运动到 ② → 点击后运动到 ③。

```text
（屏外）Position1 ──移动──► Position2 ──点击──► Position3（贴圆）
                              待命                    插上 → parent = Circle
```

预览时可在每个 Position 下临时挂一根 Pin（本地 0,0）；调间距时看整根针是否出屏、①→② 是否够「滑入感」、②→③ 是否太短。

> [!tip]
> 三个点尽量 **同一竖直线**（同 X、不同 Y），后面移动只需改 Y，逻辑简单。

定位调完后：Position 下临时预览用的 Pin 可 **销毁** 或 **先禁用**；以后要微调位置再启用即可。正式针一律由代码生成。

---

## 6. 针的生成（见缝插针 · P08）

> [!summary]
> 定位点调完后，临时预览针可销毁或禁用。正式流程用 **`GameManager`** 管生成（以及以后的胜负）：`pinSpawn` = `instantiate(pinPrefab)` → `addChild` 到管理器下 → 对齐 `p1`。开局 `start` 刷一根；**运动交给针自己**（P09）。

### 6.1 承接上一节

| 事项 | 做法 |
| --- | --- |
| Position 下的预览 Pin | **销毁**或**先禁用**；微调位置时再启用即可 |
| 正式的针 | 一律由代码 `instantiate`，不再手摆 |
| 本节范围 | 只做 **生成**；生成后移到 p2、点击插向 p3 放到下节 |

### 6.2 为什么要有 GameManager

课上把「生成针 + 失败/胜利判定」收拢到一个管理脚本，避免逻辑散落在各个 Pin 上。

| 步骤 | 操作 |
| --- | --- |
| 1 | 在 `scripts` 下新建脚本 `GameManager.ts` |
| 2 | 场景建 **空节点**，也叫 `GameManager`，把脚本挂上去 |
| 3 | 管理器本地位置建议放在 **(0, 0)**（与课上一致，后面本地坐标才省事） |
| 4 | 检查器赋值：`p1`/`p2`/`p3` ← 三个 Position；`pinPrefab` ← Prefab 资源 |

> [!note] ASR 校正
> 字幕里的 *pinspoon* → **`pinSpawn`**；*instinstate* → **`instantiate`**；*list node.add children* → **`this.node.addChild`**；*负值* → **赋值**。

### 6.3 生成流水线

```text
start()
  └─ pinSpawn()
        ├─ instantiate(pinPrefab)     → 得到 const pin
        ├─ this.node.addChild(pin)    → 挂到 GameManager 下（方便在层级里找）
        └─ pin.setPosition(p1.position) → 初始落在一号位（屏外）
```

本节生成只用 `p1`；`p2`/`p3` 先挂上引用，留给移动与插入。

### 6.4 脚本：`GameManager.ts`

```ts
import { _decorator, Component, Node, Prefab, instantiate } from 'cc';
const { ccclass, property } = _decorator;

@ccclass('GameManager')
export class GameManager extends Component {
    @property(Node)
    p1: Node | null = null;

    @property(Node)
    p2: Node | null = null;

    @property(Node)
    p3: Node | null = null;

    @property(Prefab)
    pinPrefab: Prefab | null = null;

    start() {
        this.pinSpawn();
    }

    /** 在一号位生成一根针 */
    pinSpawn() {
        if (!this.pinPrefab || !this.p1) return;

        const pin = instantiate(this.pinPrefab);
        this.node.addChild(pin);

        // 课上：本地坐标。前提见下方 warning
        pin.setPosition(this.p1.position);

        // 更稳妥（父节点坐标不一致时）：
        // pin.setWorldPosition(this.p1.worldPosition);
    }
}
```

| API / 字段 | 作用 |
| --- | --- |
| `@property(Node) p1/p2/p3` | 三个定位点；本节生成只用 `p1` |
| `@property(Prefab) pinPrefab` | 要实例化的针预制体（默认 `null`，检查器拖入） |
| `instantiate(prefab)` | 克隆出节点树实例 |
| `this.node.addChild(pin)` | 先挂在 `GameManager` 下 |
| `pin.setPosition(this.p1.position)` | 初始落在一号位（课上写法） |
| `start()` | 游戏开始先刷一根针 |

### 6.5 本地坐标 vs 世界坐标

课上先试本地：`pin.setPosition(this.p1.position)`。

| 情况 | 说明 |
| --- | --- |
| 为何课上本地能用 | `GameManager` 本地约在 **(0,0)**，与 Position 同挂在 Canvas 下，两边「本地坐标」对齐 |
| Canvas 自身 | 设计分辨率下 Canvas 世界位置常是中心（课上提到约 `360, 640`），不等于管理器本地原点 |
| 更稳妥写法 | `pin.setWorldPosition(this.p1.worldPosition)`——父节点挪了也不容易错位 |

> [!warning] 本地坐标前提
> `setPosition(p1.position)` 只有在「Pin 的父节点」与「p1 的父节点」坐标系对齐时才等价。若把 `GameManager` 挪离原点，或 Position 换了父节点，请改用世界坐标。

### 6.6 运行时怎么确认生成成功

1. 先给检查器四个引用赋值（未拖会生成失败或什么都没有）。
2. 运行后预览里可能 **看不见**——针还在 **屏外一号位**，属正常。
3. 打开 **层级管理器**：`GameManager` 下应出现新的 `Pin`。
4. 或点 **暂停**，在场景/预览底区能看到屏外那根针。

### 6.7 和下一节的分工

| 谁 | 管什么 |
| --- | --- |
| `GameManager` | `pinSpawn` 生成；以后胜负判定 |
| **针自身脚本**（P09） | 提供 `moveTo`；生成后由管理器调用，移到 **p2** |
| **点击插入**（P10） | 管理器监听触摸，让 `currentPin` 冲向 **p3**，再刷下一根 |

课上原话：生成完要控制它运动到二号位——**运动能力写在针上**，管理器负责「何时、移向哪」。

---

## 7. tween 控制针的运动（见缝插针 · P09）

> [!summary]
> 在 Prefab 上挂 **`Pin.ts`**，对外只暴露 `moveTo(目标, 秒数)`。内部用系统 **`tween(this.node).to(...).start()`** 做位置插值。`GameManager.pinSpawn` 生成后取出 `Pin` 组件，移到 **p2**；时长用 `@property moveDuration`（课上约 0.5s）。

### 7.1 挂脚本到 Prefab

1. 新建 `Pin.ts`，挂到针 Prefab 根节点（双击 Prefab 编辑，或改场景实例后 **Apply**）。
2. 职责：给针提供「移到指定位置」的能力，供外界调用——不在 `Pin.start` 里写死终点。

### 7.2 `moveTo` + tween

位置动画和颜色渐变同一套路：某个属性从当前值变到目标值。

```ts
import { _decorator, Component, Vec3, tween } from 'cc';
const { ccclass } = _decorator;

@ccclass('Pin')
export class Pin extends Component {
    /** 在 duration 秒内移动到 targetPosition（本地坐标） */
    moveTo(targetPosition: Vec3, duration: number) {
        tween(this.node)
            .to(duration, { position: targetPosition }, { easing: 'smooth' })
            .start();
    }
}
```

| 片段 | 含义 |
| --- | --- |
| `tween(this.node)` | 对 **节点** 做动画（位置在 `node` 上） |
| `.to(duration, { position }, { easing })` | 持续 `duration` 秒，把 `position` 插到目标；`easing: 'smooth'` 曲线平滑 |
| `.start()` | 真正开始播 |
| 链式写法 | `tween(...).to(...).start()`，课上称「链式编程」 |

> [!tip]
> 也可用每帧自己算位移（飞机大战那套）；本节用 tween 省事。先会用，曲线细节可后查。

### 7.3 生成后移到二号位

`GameManager` 增加可调时长，生成后调用 `moveTo`：

```ts
@property
moveDuration = 0.5; // 秒；不是速度

pinSpawn() {
    if (!this.pinPrefab || !this.p1 || !this.p2) return;

    const pinNode = instantiate(this.pinPrefab);
    this.node.addChild(pinNode);
    pinNode.setPosition(this.p1.position);

    const pin = pinNode.getComponent(Pin);
    if (pin) {
        pin.moveTo(this.p2.position, this.moveDuration);
    }
}
```

| 注意 | 说明 |
| --- | --- |
| 变量名 | 节点叫 `pinNode`，组件叫 `pin`，避免和 Prefab 字段糊在一起 |
| `moveDuration` | 单位是 **秒**（课上曾误起名 `moveSpeed`，随即改掉） |
| 属性要用 `this.` | `this.p2`、`this.moveDuration` |
| 调试 | 可先在 `Pin.start` 里 `moveTo(new Vec3(0,0,0), 3)` 验证 tween，确认后删掉，改由管理器驱动 |

运行效果：每刷一根针，约 0.5s 从屏外滑到待命点；间距不满意就调 Position2，不必改代码。

---

## 8. 控制针的插入（见缝插针 · P10）

> [!summary]
> 针就位后，用 **`input` 监听 `TOUCH_START`**（含鼠标按下）。`GameManager` 记住 **`currentPin`**；点击时 `moveTo(p3)`，再立刻 `pinSpawn()` 补下一根待命针。插入时长可把 `moveDuration` 调到约 **0.2s**。插上后跟圆转 → 下节。

### 8.1 流程

```text
pinSpawn → 落在 p1 → moveTo(p2) 就位
                ↓
         玩家 TOUCH_START
                ↓
    currentPin.moveTo(p3)  ← 往上插
                ↓
         再 pinSpawn()     ← 屏幕下方补新针
```

### 8.2 注册 / 注销触摸

事件一般在 **`onLoad`** 注册、**`onDestroy`** 注销（成对出现，少留隐患）。

```ts
import { input, Input } from 'cc';

onLoad() {
    input.on(Input.EventType.TOUCH_START, this.onTouchStart, this);
}

onDestroy() {
    input.off(Input.EventType.TOUCH_START, this.onTouchStart, this);
}
```

| 点 | 说明 |
| --- | --- |
| `Input.EventType.TOUCH_START` | 触摸开始；桌面预览里对应鼠标按下 |
| 第 2 参 | 回调：`this.onTouchStart` |
| 第 3 参 | `this`，保证回调里 `this` 仍是组件 |
| 不写 `off` | 多数情况也能跑；课上仍建议注册/注销成对 |

> [!note] ASR 校正
> *unload* → **`onLoad`**；*on Detroit* → **`onDestroy`**；*ontouch start* → **`TOUCH_START` / `onTouchStart`**；*pin.spot* → **`pinSpawn`**；*cancel.error* → **`console.error`**。

### 8.3 记住当前针：`currentPin`

点击时要动的是「上一根已生成、正在待命」的那根，所以生成时存引用：

```ts
private currentPin: Pin | null = null;
```

- 类型用 **`Pin`**（组件）更方便直接 `moveTo`；用 `Node` 也行，调用前再 `getComponent`。
- **不要** `@property`：运行时赋值，不是检查器拖拽。

在 `pinSpawn` 里：

```ts
const pin = pinNode.getComponent(Pin);
if (!pin) {
    console.error('实例化的针身上没有 Pin 组件，请检查 Prefab');
    return;
}
this.currentPin = pin;
pin.moveTo(this.p2!.position, this.moveDuration);
```

| 点 | 说明 |
| --- | --- |
| 缺组件就 `console.error` | Prefab 上组件被误删时，控制台 **红字** 醒目（相对 `console.log`） |
| 课上说法 | 类似「护城河」：生产里要写合理的防护；这里必要性中等，但值得留 |

### 8.4 点击：插入 + 刷下一根

```ts
onTouchStart() {
    if (!this.currentPin || !this.p3) return;

    this.currentPin.moveTo(this.p3.position, this.moveDuration);
    this.pinSpawn(); // 立刻补一根新的到 p1→p2
}
```

课上手感：默认 0.5s 偏慢，把检查器里 **`moveDuration` 调到约 0.2** 更干脆。

### 8.5 本节完整 `GameManager`（相对 §6/§7 的合并）

```ts
import {
    _decorator, Component, Node, Prefab, instantiate,
    input, Input,
} from 'cc';
import { Pin } from './Pin';
const { ccclass, property } = _decorator;

@ccclass('GameManager')
export class GameManager extends Component {
    @property(Node) p1: Node | null = null;
    @property(Node) p2: Node | null = null;
    @property(Node) p3: Node | null = null;
    @property(Prefab) pinPrefab: Prefab | null = null;

    @property
    moveDuration = 0.2;

    private currentPin: Pin | null = null;

    onLoad() {
        input.on(Input.EventType.TOUCH_START, this.onTouchStart, this);
    }

    onDestroy() {
        input.off(Input.EventType.TOUCH_START, this.onTouchStart, this);
    }

    start() {
        this.pinSpawn();
    }

    onTouchStart() {
        if (!this.currentPin || !this.p3) return;
        this.currentPin.moveTo(this.p3.position, this.moveDuration);
        this.pinSpawn();
    }

    pinSpawn() {
        if (!this.pinPrefab || !this.p1 || !this.p2) return;

        const pinNode = instantiate(this.pinPrefab);
        this.node.addChild(pinNode);
        pinNode.setPosition(this.p1.position);

        const pin = pinNode.getComponent(Pin);
        if (!pin) {
            console.error('实例化的针身上没有 Pin 组件，请检查 Prefab');
            return;
        }

        this.currentPin = pin;
        pin.moveTo(this.p2.position, this.moveDuration);
    }
}
```

### 8.6 验收与未做事项

| 应看到 | 说明 |
| --- | --- |
| 开局 | 一根针从屏外滑到 p2 |
| 点击 | 该针冲向 p3；下方同时再刷一根滑入 p2 |
| 连点 | 可连续插入多根 |

| 尚未做 | 下节方向 |
| --- | --- |
| 插上后不跟圆转 | §9：tween 结束后换父到 `Circle`，并保住世界位姿 |
| 分数 UI | §10 |
| 针头相碰失败 | 课序上在跟随旋转之后；本地暂无 P12 字幕 |

---

## 9. 针跟随圆球旋转（见缝插针 · P11）

> [!summary]
> 必须先等插针 tween **播完**，再挂到圆下。给 `moveTo` 增加可选 **`parentNode`**：动画结束用 `.call`；若传了父节点，则换父。直接 `addChild` / `setParent` 会把本地坐标（和旋转）重置，针会「飞到圆心」——课上先存 **世界位置 + 世界旋转**，换父后再设回去。

### 9.1 两步，不能颠倒

| 步骤 | 为何 |
| --- | --- |
| 1. 等到达到 p3 | 没到终点就跟圆转，轨迹会错 |
| 2. 设为 Circle 子节点 | 父转子跟转（同 §3.3 / §5） |

p1→p2 **不**换父；只有插入（p2→p3）才传 `circleNode`。

### 9.2 tween 结束：`.call`

在 `.to` 与 `.start` 之间加 `.call`，动画结束执行回调：

```ts
moveTo(targetPosition: Vec3, duration: number, parentNode: Node | null = null) {
    tween(this.node)
        .to(duration, { position: targetPosition }, { easing: 'smooth' })
        .call(() => {
            if (!parentNode) return;

            // 换父会改本地变换，先保住世界位姿
            const worldPos = this.node.worldPosition.clone();
            const worldRot = this.node.worldRotation.clone();

            this.node.setParent(parentNode);
            this.node.setWorldPosition(worldPos);
            this.node.setWorldRotation(worldRot);
        })
        .start();
}
```

| 点 | 说明 |
| --- | --- |
| 第 3 参 `parentNode` | 默认 `null`；生成移向 p2 时不传 |
| `.call(fn)` | tween 播完再跑；换父逻辑写在这里 |
| `addChild` 踩坑 | 换父后本地坐标常变 **(0,0)**，针叠到圆心，预览像「消失」 |
| 只 `setParent` | 位置仍会变；课上还发现 **旋转也被重置**，针朝向全竖着像辐条 |
| 课上修法 | `getWorldPosition` / `getWorldRotation` → `setParent` → `setWorldPosition` / `setWorldRotation` |

> [!tip] API 捷径
> Creator 3.x 可用 `this.node.setParent(parentNode, true)`，第二参 **keepWorldTransform** 为 `true` 时保持世界变换。课上手写存取世界位姿，效果同类；记哪种都行。

### 9.3 GameManager：插入时传入圆

```ts
@property(Node)
circleNode: Node | null = null;

// pinSpawn：只移到 p2，不传 parent
pin.moveTo(this.p2.position, this.moveDuration);

// onTouchStart：插入并指定父为圆
this.currentPin.moveTo(this.p3.position, this.moveDuration, this.circleNode);
this.pinSpawn();
```

检查器把场景里的 **Circle** 拖到 `circleNode`。

### 9.4 验收

1. 点击插入后，针停在圆缘，并随圆旋转。
2. 层级里针应出现在 `Circle` 下，且不在圆心。
3. 多根插入后，各针相对圆的「扎入角度」应保持（世界旋转保住）。

> [!note] ASR 校正
> *Toon* → **tween**；*.call* 监测结束；*唯控* → **null**；*game measure* → **GameManager**；*get the world position* → **worldPosition / getWorldPosition**。

课末预告：两针接触 → 失败处理。本地暂无对应字幕（P12）；下一有字幕的一集是分数 UI。

---

## 10. 分数与 UI 更新（见缝插针 · P13）

> [!summary]
> Canvas 下建 **Label（ScoreLabel）** 置顶。`GameManager` 用私有 `score` + `@property(Label) scoreLabel`。更好的时机是 **插针到位** 再加分，而不是一点击就加——把 `updateScore` 抽出来，用 **单例** 让 `Pin` 在 tween `.call` 里调用。

### 10.1 搭 ScoreLabel

| 步骤 | 操作 |
| --- | --- |
| 1 | Canvas 右键 → UI 组件 → **Label**，命名 `ScoreLabel` |
| 2 | 放到画面 **最上方**；初始文字 `0` |
| 3 | 字号课上试过 80 → 100 → 200（三位数易溢出）→ 约 **180** 兼顾两三位 |
| 4 | 颜色等按需；课上几乎没改 |

### 10.2 分数数据 + 引用

```ts
@property(Label)
scoreLabel: Label | null = null;

private score = 0;
```

- `score`：**private**，不靠检查器拖。
- `scoreLabel`：检查器把 `ScoreLabel` 拖进来。

### 10.3 两种加分时机

| 时机 | 做法 | 观感 |
| --- | --- | --- |
| A. 点击时 | `onTouchStart` 里 `score++` 并改 Label | 针还在飞，分已加，略早 |
| B. 插上时（课上更推） | tween 结束（换父成功）再 `updateScore` | 针扎上才加分，更贴玩法 |

抽方法：

```ts
updateScore() {
    this.score++;
    if (this.scoreLabel) {
        this.scoreLabel.string = `${this.score}`;
    }
}
```

### 10.4 单例：让 Pin 回调到 GameManager

Pin 到位时要调管理器，课上做成简单单例（场景里只挂一个）：

```ts
private static _inst: GameManager | null = null;

public static get inst(): GameManager | null {
    return GameManager._inst;
}

onLoad() {
    GameManager._inst = this;
    input.on(Input.EventType.TOUCH_START, this.onTouchStart, this);
}
```

| 点 | 说明 |
| --- | --- |
| `static get inst` | 用属性访问：`GameManager.inst`，不必 `inst()` |
| `onLoad` 赋值 | ASR *unload* → **`onLoad`** |
| 用途 | `Pin` 不拖引用也能找到管理器 |

在 `Pin.moveTo` 的 `.call` 里，换父之后：

```ts
.call(() => {
    if (parentNode) {
        const worldPos = this.node.worldPosition.clone();
        const worldRot = this.node.worldRotation.clone();
        this.node.setParent(parentNode);
        this.node.setWorldPosition(worldPos);
        this.node.setWorldRotation(worldRot);

        GameManager.inst?.updateScore();
    }
})
```

这样只有 **传入了 parent（真正插入）** 才加分；p1→p2 滑入不加分。

### 10.5 验收

1. 开局 Label 为 `0`。
2. 每次针插到圆上并跟转后，分数 +1 且 Label 同步。
3. 仅滑入待命、未插入，分数不变。

> [!note] ASR 校正
> *RD 对象* → 创建 **Label**；*mr.score* → **`this.score`**；*string 赋值* → **`scoreLabel.string = ...`**；*加块* → 访问 getter **不加 `()`**。

---

## 11. 针头之间的碰撞检测（见缝插针 · P14）

> [!summary]
> 失败条件 = **针头碰针头**。Prefab 根 `Pin` 上挂 **`CircleCollider2D`**（半径对准针头），并在 **`Pin.ts`** 里对 `Collider2D` 注册 `Contact2DType.BEGIN_CONTACT`。Creator 3.x（Box2D）下还要同节点挂 **`RigidBody2D`**，并勾选 **Enabled Contact Listener**，否则常有碰撞体却无回调。场景里只需针带碰撞体时，发生接触即可判失败，不必再按 tag 分支。

### 11.1 组件清单（Collider + 刚体）

课上字幕主要演示了加 `CircleCollider2D`；实作时 **刚体不要漏**——否则编辑器里能看见绿圈，运行却收不到 `BEGIN_CONTACT`（或出现 `enabledContactListener` 相关空引用）。

| 组件 | 挂在哪 | 作用 |
| --- | --- | --- |
| **CircleCollider2D** | Prefab 根 `Pin`（父节点） | 圆形碰撞形状；编辑半径/偏移，对准 **PinHead** |
| **RigidBody2D** | **同一节点** `Pin` | 参与 2D 物理世界；碰撞体初始化时会查找同节点刚体 |

#### RigidBody2D 必配项

| 属性 | 建议 | 原因 |
| --- | --- | --- |
| **Type** | **Kinematic** | 针的位置由 **tween/脚本** 驱动，不是重力 Dynamic 模拟。双方若都是 **Static**，Box2D 下 **Static–Static 不碰撞** |
| **Enabled Contact Listener** | **勾选** | Box2D 模块下：不开启则 **没有碰撞回调**（官方手册强调） |
| Gravity Scale 等 | 保持默认即可 | Kinematic 不受重力；不必改成 Dynamic |

> [!warning] 只加 Collider、不加刚体？
> - **Builtin 2D**：一般有碰撞体即可出回调。
> - **Box2D**（项目默认常见）：回调挂在「开启了接触监听的刚体」上；同节点缺 `RigidBody2D` / 未勾选监听 → 检测代码形同虚设。
> - 碰撞体 `body` 字段：初始化时查找同节点刚体；找不到则为 `null`。

可选：若只要「碰到就回调」、不要物理引擎把两针弹开，可把 Collider 的 **Sensor** 勾上（传感器：有回调、无冲量分离）。本玩法用 tween 插针，Sensor 往往更省心。

项目侧确认：**项目设置 → 物理** 启用了 **2D 物理**（Box2D）。

### 11.2 编辑 CircleCollider2D

课上步骤：

1. 打开 Pin Prefab（或启用二号位预览针方便看）。
2. 根节点添加 **CircleCollider2D** → 点 **编辑**：缩小半径，把圆心 **拖到针头**，再微调到刚好盖住针头。
3. **保存 / Apply** Prefab。预览用的 Position2 下的针可再 **禁用**。

| 点 | 说明 |
| --- | --- |
| 挂在父节点 `Pin` | 脚本在 `Pin` 上 `getComponent(Collider2D)` 即可监听 |
| 只给针加碰撞 | 场景里没有别的 Collider → **一碰就是针头对针头**，回调里可先不做类型判断 |
| 不同时给大圆加 | 避免针插圆也被当成失败 |

### 11.3 代码：注册 / 注销接触

对照官方「碰撞回调」示例；`onLoad` 注册、`onDestroy` 注销。

```ts
import {
    _decorator, Component, Collider2D, Contact2DType, IPhysics2DContact,
} from 'cc';
const { ccclass } = _decorator;

@ccclass('Pin')
export class Pin extends Component {
    onLoad() {
        const collider = this.getComponent(Collider2D);
        if (collider) {
            collider.on(Contact2DType.BEGIN_CONTACT, this.onBeginContact, this);
        } else {
            console.error('针没有添加碰撞器，无法进行碰撞回调');
        }
    }

    onDestroy() {
        const collider = this.getComponent(Collider2D);
        if (collider) {
            collider.off(Contact2DType.BEGIN_CONTACT, this.onBeginContact, this);
        }
        // 注销不必 else：没有碰撞体就无需 off
    }

    onBeginContact(
        selfCollider: Collider2D,
        otherCollider: Collider2D,
        contact: IPhysics2DContact | null,
    ) {
        // P14：先打日志确认能收到；P15 再调 gameOver
        console.log('contact', selfCollider, otherCollider);
    }

    // moveTo(...) 同 §9，略
}
```

| 点 | 说明 |
| --- | --- |
| `getComponent(Collider2D)` | 基类即可，不必写死 `CircleCollider2D` |
| 注册缺组件 → `console.error` | 课上「安全校验 + else」：否则会静默不跑，难查 |
| 注销不加 else | 没有组件就不 off，不影响功能 |
| 日志打出 **两次** | 每根针都挂了监听，A↔B 各触发一次 → **正常** |

> [!note] ASR 校正
> *unload* → **`onLoad`**；*contact / begincontact* → **`Contact2DType.BEGIN_CONTACT`**；*onDetroit* → **`onDestroy`**；*副物体* → **父节点**；*暂时进用* → **暂时禁用**。

### 11.4 验收（本节）

1. Prefab：`Pin` 上同时有 **RigidBody2D（Kinematic + 接触监听）** 与 **CircleCollider2D（盖住针头）**。
2. 两根已插针的头重叠时，控制台出现接触日志（通常成对两次）。
3. 若无日志：查刚体类型是否双方 Static、是否漏勾 Enabled Contact Listener、2D 物理是否开启。

下节：在回调里调用 `GameManager.gameOver`（注意防重入）。

---

## 12. 游戏结束逻辑（见缝插针 · P15）

> [!summary]
> `GameManager.gameOver()`：用 **`isGameOver`** 保证只处理一次（两针各回调一次会进两次）。结束时 **`Circle.stopRotate()`**，并在 **`onTouchStart`** 里若已结束则不再发射。结束动画（界面放大、改背景色）留到下节。

### 12.1 清理与入口

- 可删掉早先为观察旋转加在圆边缘的 **标记子节点**（§3.3），正式玩法已有针可视化旋转。
- 碰撞发生 → `Pin` 调 `GameManager.inst.gameOver()`。

### 12.2 防重复：`isGameOver`

一次接触 → 两根针各 `BEGIN_CONTACT` → **`gameOver` 会被叫两次**。用布尔闩锁：

```ts
private isGameOver = false;

gameOver() {
    if (this.isGameOver) return;
    this.isGameOver = true;

    // 停转、禁发射等只走一遍
    const circle = this.circleNode?.getComponent(Circle);
    circle?.stopRotate();
}
```

| 次序 | `isGameOver` | 行为 |
| --- | --- | --- |
| 第一次进入 | `false` | 执行逻辑，再设为 `true` |
| 第二次进入 | `true` | 立刻 `return` |

### 12.3 停止圆旋转：`Circle`

```ts
// Circle.ts
private isRotate = true; // 默认继续转

update(deltaTime: number) {
    if (!this.isRotate) return;
    this.node.angle -= this.rotateSpeed * deltaTime;
}

stopRotate() {
    this.isRotate = false;
}
```

`gameOver` 里：`this.circleNode.getComponent(Circle)?.stopRotate()`。

### 12.4 结束后禁止再插针

```ts
onTouchStart() {
    if (this.isGameOver) return;
    // ... moveTo(p3) + pinSpawn
}
```

### 12.5 Pin 回调接上结束

```ts
onBeginContact(/* ... */) {
    GameManager.inst?.gameOver();
}
```

### 12.6 验收与未做

| 应看到 | 说明 |
| --- | --- |
| 两针头相碰 | 圆立刻停转；再点屏幕不再出新针 |
| 只结束一次 | 逻辑/副作用不因双回调执行两遍 |

| 尚未做（下节） | 说明 |
| --- | --- |
| 结束动画 | 整个界面放大；背景颜色变化 |

> [!note] ASR 校正
> *easegame over* → **`isGameOver`**；*board / Bolling* → **`boolean`**；*retay / retend* → **`return`**；*默认为处*（旋转标志）→ 默认 **`true`（保持转）**；*circleNote* → **`circleNode`**。

---
