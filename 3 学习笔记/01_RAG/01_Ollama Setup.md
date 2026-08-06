---
title: Ollama Setup
aliases:
  - Ollama 安装与命令
  - Ollama CLI
  - Modelfile
  - 本地 LLM Serving
created: 2026-07-31
updated: 2026-08-06
series: 本地 RAG
part: 1
source: 01. Ollama Setup（可删）· 字幕 005–020（可删）
tags:
  - type/literature-note
  - topic/ollama
  - topic/local-rag
  - topic/modelfile
  - topic/gguf
  - status/draft
---

# Ollama Setup（安装、模型与本地 API）

> [!summary]
> **本地 RAG · 第 1 部分**。Ollama 把「下模型 + Serving + HTTP API」打包成本地服务（默认 `http://localhost:11434`）。本笔记建立：**装什么 → 怎么选模型 → 日常 CLI / 自定义人设 → 原始 API**，为后续 LangChain 接本地模型打底。

环境依赖见 [[杂项]]。下一篇：[[02_Langchain]] · [[Chat Prompt Templates]]。

## 本章目录

| 章节             | 学什么                                        |
| -------------- | ------------------------------------------ |
| §1 为什么是 Ollama | Serving 链路；GUI / CLI / API 三位一体            |
| §2 选模型         | 标签、量化、Benchmark、按任务选型                      |
| §3 UI 与设置      | Context、联网、局域网；Vision 拖文件速览                |
| §4 日常 CLI      | pull / run / list / show / rm / ps / stop  |
| §5 自定义模型       | Modelfile `create` vs 会话里 `/set` + `/save` |
| §6 Raw API     | `/api/generate` 与 `/api/chat`              |
| §7 本地 GGUF     | 何时用（含 Uncensored）、从哪下、怎么 `create`、推荐试跑模型   |
| 文末速查           | 命令与端点一览                                    |

---

## 1. 为什么是 Ollama

### 1.1 调用方式对比

**自己拆开搭**

```text
模型权重
  → Serving（vLLM / 其它）
  → 自建 API
  → 用户 / 应用
```

**用 Ollama**

```text
ollama pull / run
  → 内置 Serving
  → http://localhost:11434
  → GUI / CLI / LangChain …
```

| 场景 | 自己搭 Serving | Ollama |
| --- | --- | --- |
| 下模型 | 另找源 | `pull` / 官网一键 |
| 起服务 | 自己配 | 安装即有（GUI 或 `serve`） |
| 给框架用 | 自己暴露 HTTP | 默认 `11434` |
| 对话试玩 | 另找前端 | 自带 GUI + `run` 会话 |

### 1.2 装完你得到什么

从 [ollama.com](https://ollama.com) 安装（Win / Linux / macOS）后：

| 入口 | 用途 |
| --- | --- |
| GUI | 选模型、看 thinking、拖文件、改 Settings |
| CLI | `ollama …`；关 UI 也能用 |
| API | `localhost:11434`；LangChain 的 `base_url` |

> [!tip]
> 系统托盘有进程图标时，服务通常已在跑。`ollama run` 也会自动拉起服务。

### 1.3 本节要点

| 要点 | 说明 |
| --- | --- |
| 定位 | 本地 LLM 运行时，不是 RAG 框架本身 |
| 默认地址 | `http://localhost:11434` |
| 后面怎么用 | 应用只认 API；先保证模型 `pull` 好、服务活着 |

---

## 2. 选模型

### 2.1 在哪里看

- 官网 [Models](https://ollama.com) / Library：简介、参数量、标签
- GUI 列表只是**精选子集**；不全就去官网搜，复制 `pull` / `run` 命令
- ☁ = Cloud（远程、要额度）；无云图标 = 本地；下载图标 = 还没权重

本地推理占显存：首次加载慢。课程口径可用显存约 **4–6 GB**（≥6 GB 更稳）。

### 2.2 标签怎么读

| 标签 / 类型 | 含义 | 选型例子（课程口径） |
| --- | --- | --- |
| Thinking | 先推理链再答；更准更慢 | Qwen3、DeepSeek R1 |
| Vision | 可看图 / 部分可扫 PDF | Gemma3、Llama 3.2 Vision、LLaVA |
| Tools | 适合函数 / 工具调用 | GPT-OSS、Qwen3、DeepSeek 系 |
| Embeddings | RAG 向量 | `nomic-embed-text`、`embedding-gemma` |
| Cloud | 本地装不下的超大模型 | 数百 GB 级 VL 等 |

原则：**先定任务类别 → 再看能否本地跑 → 再权衡速度 vs thinking**。

### 2.3 读模型卡（以 Qwen3 为例）

打开 [library/qwen3](https://ollama.com/library/qwen3)。`ollama run qwen3` 对应**默认规格**（常见为量化后的 8B 档，以页面为准）。

重点看：

- **量化**（如 `Q4_K_M`）：体积 / 显存 vs 精度；全精度需求远高于量化版
- 默认 `temperature` / `top_p`、对话模板、tool / think 格式
- **Benchmark 图**：数学、代码、指令、工具调用等轴（GPQA、AIME、LiveCodeBench、Arena Hard、BFCL 等）

Thinking 版在难题上往往明显好于非 thinking，但更慢。本地可自测难题，再用更强模型当评判（把「题目 + 我的答案」交给它判对错）。

> [!note]
> LLM 输出是概率性的；工具同参返回是确定的。选型时别只看参数量口号。

---

## 3. UI 与设置

### 3.1 常用 Settings

| 项 | 记住什么 |
| --- | --- |
| Context length | 窗口越大越慢；数据不超窗可调小。UI 常建议 **64K**；API 未传参时常跟 UI |
| Model location | 本地库目录（manifest + 编码存储，不是随便打开的裸文件） |
| Expose to network | 默认仅本机；开了 → `http://<本机IP>:11434` |
| 实时搜索 | 开：可搜网引 URL；关：答不了「现在天气」类 |
| Airplane mode | 切断 Ollama 联网 |
| API Key | Cloud 模型用 |

### 3.2 Vision：拖文件做「假 RAG」直觉

UI **没有上传按钮** → **拖拽** 或 **Ctrl+C / V** 贴进对话。

```text
PDF / 图片
  → 选 Vision 模型（如 Gemma3）
  → 提问
  → 快速验证「上下文里有没有答案」
```

正式 RAG 仍要自己做加载 / 分块 / 检索；Ollama 只当 LLM 后端。Qwen3 默认文本向，**不要指望它看图**。

---

## 4. 日常 CLI 工作流

关 UI 也能干活。先记这条主路径：

```text
ollama pull <model>     # 只下载
ollama run <model>      # 无则先 pull，再进对话（有多轮记忆）
  … 对话 …
/bye                    # 退出会话
```

### 4.1 管理本地模型

```bash
ollama list              # 有哪些、多大
ollama show qwen3        # 架构、ctx、量化、license…
ollama rm <model>        # 删除（UI 同步没）
ollama ps                # 谁在跑、占多少
ollama stop <model>      # 卸掉运行实例（再问会重载）
```

| 命令 | 注意 |
| --- | --- |
| `serve` | 前台起 API；关终端服务停。与 GUI 启动**二选一**即可 |
| `cp A B` | 复制整份权重，占磁盘；改参更推荐 Modelfile / 运行时参数 |
| `push` | 上传/分享向，本课未展开 |
| 断点续传 | 大模型 `pull` 中断一般可继续 |

显存够可并行多模型；不够会卸旧载新。在对话里时，先 `/bye` 再跑 `show` 等更干净。

### 4.2 会话内 `/` 命令（`run` 之后）

| 命令 | 作用 |
| --- | --- |
| `/set …` | parameter、history/nohistory、verbose、think/nothink、format json… |
| `/show info` / `/show modelfile` | 当前信息 / 完整 Modelfile |
| `/load <model>` | 会话内换模型 |
| `/save <name>` | **固化当前配置**为新模型 |
| `/clear` | 清上下文 |
| `/bye` | 退出 |
| `/?` | 帮助；多行输入可用 `"""` |

Thinking 模型嫌慢：`/set nothink`。

---

## 5. 自定义模型：锁人设与默认参数

目标一样：**固化 SYSTEM + PARAMETER**。两条路：

```text
路径 A（文件）  Modelfile → ollama create → run
路径 B（交互）  run 基础模型 → /set 试效果 → /save 新名
```

| | 路径 A Modelfile | 路径 B `/save` |
| --- | --- | --- |
| 适合 | 要进仓库、可复现 | 边聊边定人设 |
| 是否改基础模型 | 否，生成新名字 | 否，只存当前会话配置 |
| 典型命令 | `ollama create sheldon -f modelfile.txt` | `/save sherlock` |

### 5.1 Modelfile 最小例子（模型属性创建）

文档：[modelfile.md](https://github.com/ollama/ollama/blob/main/docs/modelfile.md)
https://github.com/ollama/ollama/blob/main/docs/modelfile.mdx
```text
FROM llama3.2

PARAMETER temperature 0.5
PARAMETER num_ctx 1024

SYSTEM You are Dr. Sheldon Cooper...（人设全文略）
```

```bash
ollama create sheldon -f modelfile.txt
ollama run sheldon
```

核心三件：`FROM`（库内模型名）→ `PARAMETER` → `SYSTEM`。

### 5.2 Message 路径最小例子

```text
/set parameter temperature 0.5
/set parameter num_ctx 2048
/set system You are Sherlock Holmes...
/save sherlock
```

`/set nohistory` / `/set history` 开关多轮记忆；`/set verbose` 看耗时与 token 速率。

> [!note]
> 与 [[Chat Prompt Templates]] 的关系：Modelfile 把人设**焊在模型上**；代码里用 `SystemMessage` / 模板则是**每次调用动态换角色**。后面会对照。

---

## 6. Raw API（给框架打底）

文档：[api.md](https://github.com/ollama/ollama/blob/main/docs/api.md)。默认**流式**；要整包 JSON 就 `"stream": false`。

```text
应用 / LangChain
  → POST /api/chat 或 /api/generate
  → localhost:11434
  → 本地模型
```

**单轮补全**

```bash
curl http://localhost:11434/api/generate -d "{
  \"model\": \"qwen3\",
  \"prompt\": \"Why is the sky blue?\",
  \"stream\": false
}"
```

**多轮对话**

```bash
curl http://localhost:11434/api/chat -d "{
  \"model\": \"qwen3\",
  \"messages\": [
    {\"role\": \"user\", \"content\": \"why is the sky blue?\"}
  ],
  \"stream\": false
}"
```

还常见：`system`、`options`、`format`（约束 JSON）、`think`、`images`、`keep_alive`。

> [!tip]
> Windows 多行 `curl` 用 **Git Bash** 更省事。业务里通常不再手写 curl，由 LangChain 等封装。

---

## 7. 本地 GGUF 导入（可选）

日常优先 `ollama pull`。本节是**旁路**：手里已有 `.gguf`（或库里没有的量化 / 微调版）时，用 Modelfile 登记进 Ollama，之后仍走同一套 CLI / API。

官方说明：[Importing a model](https://docs.ollama.com/import) · [Modelfile](https://github.com/ollama/ollama/blob/main/docs/modelfile.md)

### 7.1 GGUF 是什么、何时用

**GGUF**（GPT-Generated Unified Format）是 llama.cpp 生态常用的本地权重格式：单文件、自带元数据、常带量化（如 `Q4_K_M`）。Ollama 内部也大量基于同类运行时；官方库省去的是「你自己找文件 + 写 TEMPLATE」这一步。

| 场景 | 建议 |
| --- | --- |
| Ollama Library 已有同款 | 直接 `pull`，别折腾 GGUF |
| 要特定量化 / 仓库里没有的变体 | 下 GGUF → `create` |
| 要 **Uncensored / Abliterated** 等库外变体 | 几乎只能走 GGUF → `create`（见下） |
| 自己 / 别人微调后的 GGUF | 同上；注意 TEMPLATE 与底座是否匹配 |
| 只想验证「导入流程通不通」 | 先下 **≤2B / 3B** 的 `Q4_K_M` 试跑 |

与 §5 相同流程，差别只在 **`FROM`**：

| `FROM` 写法 | 含义 |
| --- | --- |
| `FROM llama3.2` | 继承 Ollama 库里已有模型 |
| `FROM ./model.Q4_K_M.gguf` | 相对路径（`create` 时 cwd 要对） |
| `FROM C:/models/xxx.Q4_K_M.gguf` | 绝对路径；Windows 用 `/` 或 `\\` |

#### Uncensored 与 GGUF（常见误区）

**GGUF 只决定「怎么存、怎么加载」**，不决定「会不会拒答 / 能不能写敏感内容」。后者看**权重本身**有没有安全对齐（RLHF / 拒答训练等）。

| 名称常见写法 | 大致含义 |
| --- | --- |
| **Instruct / Chat**（官方） | 有对齐；对违法、露骨、危险请求更易拒答或弱化 |
| **Uncensored** | 社区微调：弱化 / 去掉拒答倾向，仍可能保留部分能力与风格 |
| **Abliterated** | 一类去对齐手法（常改拒绝方向的内部表征）；拒答更少，质量不稳定 |
| **Dolphin / Wizard 等系列** | 历史上常见的「更少审查」微调品牌；底座与年份不同，别当通用标签 |

课程里提到 Uncensored，本质是：**官方 `ollama pull` 没有你要的变体时，从 HF 下对应 GGUF，再用 Modelfile `create` 挂进本地**——和下一篇 LangChain 换 `model=` 是同一套 Serving，只是权重名不同。

选型要点：

1. HF 搜 `底座名 + uncensored` / `abliterated` + `GGUF`；仍优先 **Instruct 系变体**，别下成 Base。
2. 读 README：说明「去掉哪些拒答」、是否还带 NSFW 数据、许可证是否允许你的用途。
3. 能力常略逊同尺寸官方 Instruct（对齐被拆掉时，指令遵循 / 幻觉也可能变差）；先小模型试流程。
4. 本地 Ollama **没有**云端那种统一内容审核；边界完全取决于权重 + 你自己的提示与用途。

> [!warning]
> 学 RAG / Agent：**官方 Instruct + `pull` 足够**。Uncensored 只在你明确需要更少拒答、且能自行合规时才下；勿用于违法或有害生成。许可证与仓库说明为准。

### 7.2 从 Hugging Face 找 GGUF

主站：[huggingface.co](https://huggingface.co/) · 模型列表可按关键词筛：[Models · search=gguf](https://huggingface.co/models?search=gguf&sort=trending)

**在页面上怎么找**

1. 搜索框输入：`Qwen2.5-1.5B-Instruct GGUF`（模型名 + `GGUF`）。
2. 打开仓库后看 **Files and versions**：点具体 `.gguf` 右侧下载；或复制仓库名给 CLI。
3. 优先看：仓库是否带 `GGUF` 标签、README 里的量化表、下载量 / 最近更新、许可证（License）。

| 来源类型 | HF 入口 | 怎么选 |
| --- | --- | --- |
| 量化社区仓 | [bartowski](https://huggingface.co/bartowski)、[lmstudio-community](https://huggingface.co/lmstudio-community)、[unsloth](https://huggingface.co/unsloth) | 同模型多档量化 + imatrix；README 常推荐默认用 `Q4_K_M` |
| 官方 GGUF | 如 [Qwen](https://huggingface.co/Qwen) 下的 `*-Instruct-GGUF` | 模板 / 许可证更正统；文件名常小写 `qwen2.5-…-q4_k_m.gguf` |
| 老牌量化仓 | [TheBloke](https://huggingface.co/TheBloke) | 小模型、旧卡仍可用；新大模型优先 bartowski / 官方 |

下载注意：

1. 选 **Instruct / Chat / IT**，不要 Base。
2. 量化优先 **`Q4_K_M`**；紧再 `Q3_K_M` / `IQ4_XS`；要质量再 `Q5_K_M` / `Q8_0`。
3. bartowski 仓多为 **imatrix** 量化，同档位往往更划算。
4. 只下**单个** `.gguf`，别把整个仓库 clone 下来（官方 README 也这么建议）。

> [!tip]
> 课程口径显存约 **4–6 GB**：练导入用 **1B–3B + Q4_K_M**；正式对话再上 7B/8B，并给 KV cache 留余量。

### 7.3 推荐试跑模型（HF 直链）

目标：文件小、流程短、中文 / 指令可用。下表「推荐文件」以各仓库 README 为准（体积约数，会随量化脚本微调）。

| 用途 | HF 仓库 | 推荐文件 | 约体积 |
| --- | --- | --- | --- |
| **首选练导入** | [bartowski/Qwen2.5-1.5B-Instruct-GGUF](https://huggingface.co/bartowski/Qwen2.5-1.5B-Instruct-GGUF) | `Qwen2.5-1.5B-Instruct-Q4_K_M.gguf` | ~1.0 GB |
| 官方同款备选 | [Qwen/Qwen2.5-1.5B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF) | `qwen2.5-1.5b-instruct-q4_k_m.gguf` | ~1.1 GB |
| 稍大一点、仍好跑 | [Qwen/Qwen2.5-3B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF) | `qwen2.5-3b-instruct-q4_k_m.gguf` | ~2 GB |
| 英文生态常见 | [bartowski/Llama-3.2-3B-Instruct-GGUF](https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF) | `Llama-3.2-3B-Instruct-Q4_K_M.gguf` | ~2.0 GB |
| **冒烟最小** | [TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF) | `tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf` | ~0.67 GB |

为何这样排：Qwen2.5 小 Instruct 中文好、和本系列路线一致；Llama 3.2 文档例子多；TinyLlama 只验证 `create` 通不通。

**用 Hugging Face CLI 只下单个文件**（需先 `pip install -U huggingface_hub`）：

```bash
# 首选：bartowski Qwen2.5 1.5B Q4_K_M（约 1 GB）
huggingface-cli download bartowski/Qwen2.5-1.5B-Instruct-GGUF ^
  --include "Qwen2.5-1.5B-Instruct-Q4_K_M.gguf" ^
  --local-dir D:\models\gguf

# 官方 Qwen 仓（文件名小写）
huggingface-cli download Qwen/Qwen2.5-1.5B-Instruct-GGUF ^
  qwen2.5-1.5b-instruct-q4_k_m.gguf ^
  --local-dir D:\models\gguf

# 冒烟：TinyLlama
huggingface-cli download TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF ^
  --include "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ^
  --local-dir D:\models\gguf
```

浏览器：打开仓库 → Files → 点文件名旁下载图标。也可在 [HF 模型页](https://huggingface.co/models?search=Qwen2.5-Instruct+GGUF) 继续搜更大规格。

能 `ollama pull` 到官方同款时，**不必**为「用模型」再下 GGUF；本节只练旁路。

### 7.4 导入步骤

**1. 固定目录**（路径无空格更省心）

```text
D:\models\gguf\
  Qwen2.5-1.5B-Instruct-Q4_K_M.gguf
  Modelfile
```

**2. 写最小 Modelfile**

```text
FROM ./Qwen2.5-1.5B-Instruct-Q4_K_M.gguf
```

或绝对路径：

```text
FROM D:/models/gguf/Qwen2.5-1.5B-Instruct-Q4_K_M.gguf
```

需要时再加（与 §5 相同）：

```text
PARAMETER temperature 0.7
PARAMETER num_ctx 4096

SYSTEM You are a helpful assistant.
```

**3. 登记并试跑**

```bash
cd D:\models\gguf
ollama create qwen25-1.5b-gguf -f Modelfile
ollama run qwen25-1.5b-gguf
ollama show qwen25-1.5b-gguf
```

`create` 会把权重纳入 Ollama 本地库；之后可像普通模型一样给 LangChain 的 `base_url` 用。改 Modelfile 后**同名再 `create` 一次**即覆盖配置。

### 7.5 TEMPLATE 与常见坑

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| 能跑但答非所问 / 不听话 | 缺或错了对话 **TEMPLATE** | 对照模型卡 / README；或先 `pull` 官方同系，`/show modelfile` 抄 TEMPLATE |
| `create` 找不到文件 | 相对路径 cwd 不对 | 改绝对路径，或 `cd` 到 gguf 同目录 |
| Windows 路径炸 | `\` 被转义吃掉 | 用 `D:/...` 或 `D:\\...` |
| 导入成功但 OOM / 极慢 | 量化太大或 ctx 开太大 | 换更小量化；`PARAMETER num_ctx` 先 2K–4K |
| 角色戏崩、乱码特殊 token | Base 模型或模板不匹配 | 换 Instruct；核对 `<|im_start|>` 等标记 |

LoRA / adapter 的 GGUF 另用 `ADAPTER` 挂到**同一底座**上，见官方 Import 文档；本课主路径用整模 GGUF 即可。

> [!warning]
> 教育向：只学「如何挂第三方权重」。未对齐 / 未审计的模型可能弱化安全边界；勿用于违法或有害生成。许可证以 HF 仓库为准（部分权重禁止商用）。

---

## 文末速查

```bash
# 生命周期
ollama pull <model>
ollama run <model>          # 内：/set /show /load /save /clear /bye
ollama list | show | ps | stop | rm | cp
ollama create <name> -f <Modelfile>
ollama serve                # 可选；与 GUI 二选一

# 端点
# http://localhost:11434
# POST /api/generate | POST /api/chat
```

## Windows环境配置
```
OLLAMA_HOST=0.0.0.0:11434
OLLAMA_ORIGINS=*
```
## 相关笔记

- [[杂项]] — Conda / PyTorch / Jupyter
- [[02_Langchain]] — 接本地 Ollama
- [[Chat Prompt Templates]] — 消息角色与提示模板（动态人设）
