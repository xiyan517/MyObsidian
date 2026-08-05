---
title: Prompt Templates
aliases:
  - Chat Prompt Templates
  - 提示模板
  - LLM Prompt Templates
created: 2026-08-01
updated: 2026-08-01
series: 本地 RAG
part: 3
source: Prompt Templates.ipynb（可删）· 字幕 037–042（可删）
tags:
  - type/literature-note
  - topic/langchain
  - topic/prompt
  - topic/ollama
  - topic/local-rag
  - status/draft
---

# Prompt Templates（消息与提示模板）

> [!summary]
> **本地 RAG · 第 3 部分**。从纯字符串 `invoke`，到 `SystemMessage` / `HumanMessage` 动态换角色，再到带 `{school}` / `{topics}` / `{points}` 的 `ChatPromptTemplate`：一个标准模型，运行时换人设与问题参数。

默认：`ChatOllama(base_url="http://localhost:11434", model="qwen3")`（可换成 `llama3.2:1b` 等）。

## 本章目录

| 章节 | 学什么 |
| --- | --- |
| §1 为什么需要提示模板 | 纯字符串的局限；formatter 思路 |
| §2 消息角色与类型 | system / user / assistant / tool ↔ Message 类 |
| §3 标准模型 vs 自定义模型 | Modelfile 锁人设 vs 代码里动态设角色 |
| §4 运行时 System / Human | 同一模型切换小学老师 / 博士语气 |
| §5 提示模板类型 | `*MessagePromptTemplate` 与 `ChatPromptTemplate` |
| §6 变量填充实战 | `{school}` / `{topics}` / `{points}`；`.format` vs `.invoke` |
| 文末实践代码 | 可直接运行的完整流程 |

---

## 1. 为什么需要提示模板

### 1.1 调用方式对比

**之前：纯字符串**

```text
用户（字符串）
  → LangChain / ChatOllama
  → Ollama LLM
  → 用户（字符串，取 .content）
```

**之后：消息 / 提示模板**

```text
SystemMessage（或 System 模板）+ HumanMessage（或 Human 模板）
  → 填充变量（若用模板）
  → ChatOllama.invoke(...)
  → AIMessage（.content）
```

提示模板像 **formatter**：把带占位符的字符串格式化成正确的 System / Human / AI 消息。输出侧是 **AIMessage**，一般不再过模板。

| 场景 | 纯字符串 | 消息 / 提示模板 |
| --- | --- | --- |
| 固定系统消息 | 可用（或焊在模型上） | 可用 |
| 运行时改系统消息 | 难：要换模型或硬改代码 | 改消息或改变量即可 |
| 多轮对话 | 手动拼接字符串 | 结构化消息列表 |
| 角色与问题分离 | 混在一段里 | 清晰区分 |

### 1.2 目标

| 要点 | 说明 |
| --- | --- |
| 复用 | 改 `{变量}`，不重写整段消息代码 |
| 分层 | System / Human / AI / Tool 各司其职 |
| 结果 | **一个标准模型，多种角色与参数** |

---

## 2. 消息角色与 LangChain 类型

### 2.1 通用角色

| 角色 | 说明 |
| --- | --- |
| system | 告诉模型如何表现，并提供上下文（并非所有厂商都支持） |
| user | 用户输入（文本等） |
| assistant | 模型回复（可含文本或工具调用请求） |
| tool | 把工具执行结果回传给模型（需支持 tool calling） |
| function（遗留） | OpenAI 旧 function-calling；应改用 `tool` |

本阶段重点用 **System / Human / AI**；`AIMessageChunk`（流式）、`ToolMessage` 后面再用。

### 2.2 Ollama 模板 ↔ LangChain 消息

以 Llama 3.2 一类模型模板为例：

| Ollama 模板角色 | LangChain 消息 | 说明 |
| --- | --- | --- |
| `system` | `SystemMessage` | 系统指令 |
| `user` | `HumanMessage` | 用户输入 |
| `assistant` | `AIMessage` | 模型输出（raw 里常为 `role: assistant`） |
| `tool` | `ToolMessage` | 工具结果 |

### 2.3 LangChain Message Types

| 消息类型 | 对应角色 | 说明 |
| --- | --- | --- |
| `SystemMessage` | system | 设定角色与行为 |
| `HumanMessage` | user | 用户输入 |
| `AIMessage` | assistant | 完整模型输出 |
| `AIMessageChunk` | assistant | 流式片段 |
| `ToolMessage` | tool | 工具调用结果 |

均继承 **`BaseMessage`**。导入：

```python
from langchain_core.messages import SystemMessage, HumanMessage
```

源码大致在：

```text
langchain-core/
└── messages/
    ├── system.py  → SystemMessage
    ├── human.py   → HumanMessage
    ├── ai.py      → AIMessage
    └── tool.py    → ToolMessage
```

### 2.4 消息流向

```text
SystemMessage（系统指令）
HumanMessage（用户问题）
  ↓
ChatOllama → Ollama
  ↓
AIMessage（模型回复）
```

若开了 LangSmith，可在追踪里直接看到 system / user / assistant，便于核对组装是否正确。

---

## 3. 标准模型 vs 自定义角色模型

### 3.1 同一问题，换模型比语气

```python
from dotenv import load_dotenv
from langchain_ollama import ChatOllama

load_dotenv("./../.env")  # 可选，给 LangSmith 用

base_url = "http://localhost:11434"
question = "tell me about the earth in 3 points"

llm = ChatOllama(base_url=base_url, model="qwen3")
print(llm.invoke(question).content)

# 若本地已用 Modelfile 建过自定义模型：
# print(ChatOllama(base_url=base_url, model="sherlock").invoke(question).content)
# print(ChatOllama(base_url=base_url, model="sheldon").invoke(question).content)
```

### 3.2 系统消息放在哪

| 模型类型 | 系统消息位置 | 灵活性 | 示例 |
| --- | --- | --- | --- |
| 标准模型 | 无固定人设 | 运行时可指定 | `qwen3`、`llama3.2:1b` |
| 自定义模型 | Ollama Modelfile `SYSTEM` | 角色基本锁定 | Sherlock、Sheldon |

**方式一：Ollama 层面（固定）**

```text
FROM llama3.2
SYSTEM You are Sherlock Holmes...
```

角色写进模型，运行时不易改——Sherlock 只能 Sherlock 腔，Sheldon 只能 Sheldon 腔。

**方式二：LangChain 层面（动态，下一节）**

```python
messages = [
    SystemMessage(content="You are Sherlock Holmes..."),
    HumanMessage(content="tell me about the earth in 3 points"),
]
response = llm.invoke(messages)
```

同一标准模型可任意换角色，不必为每个人设再建一个 Ollama 模型。

---

## 4. 运行时消息：SystemMessage + HumanMessage

### 4.1 基本写法

```python
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama

llm = ChatOllama(base_url="http://localhost:11434", model="qwen3")

question = HumanMessage("tell me about the earth in 3 points")
system = SystemMessage(
    "You are elementary teacher. You answer in short sentences."
)

messages = [system, question]  # 顺序：先 System，后 Human
response = llm.invoke(messages)
print(response.content)
```

换博士人设只需改 `SystemMessage` 文本：

```python
system = SystemMessage(
    "You are phd teacher. You answer in short sentences."
)
messages = [system, question]
print(llm.invoke(messages).content)
```

对比：以前 `invoke("纯字符串")` 等价于默认 Human 输入；现在显式传 **`BaseMessage` 列表**。

### 4.2 输出风格倾向

| 角色 | 输出倾向 |
| --- | --- |
| 无系统消息 | 模型默认语气 |
| elementary teacher | 简短、偏入门 |
| phd teacher | 更专业、信息密度更高 |

### 4.3 仍不够的地方

每次换「老师类型」或「讲几点」都要**重写整段** `SystemMessage` / `HumanMessage` → 引出带变量的提示模板。

---

## 5. 提示模板类型

### 5.1 直接消息 vs 模板

| 问题 | 直接用消息 | 用提示模板 |
| --- | --- | --- |
| 改角色 | 重建整个消息 | 改 `{school}` 等变量 |
| 改主题、点数 | 改字符串 / 重写代码 | 占位符填充 |
| 复用 | 低 | 高 |

### 5.2 类型对照

| 角色 / 用途 | 直接消息 | 提示模板 |
| --- | --- | --- |
| 系统 | `SystemMessage` | `SystemMessagePromptTemplate` |
| 人类 | `HumanMessage` | `HumanMessagePromptTemplate` |
| AI | `AIMessage` | `AIMessagePromptTemplate`（少见，多用于少样本） |
| 纯文本 | — | `PromptTemplate`（静态文本 + 占位符） |
| 组合多条 | `[SystemMessage, HumanMessage]` | `ChatPromptTemplate` |

| 模板类 | 说明 |
| --- | --- |
| `SystemMessagePromptTemplate` | 生成带指令的系统消息 |
| `HumanMessagePromptTemplate` | 生成用户消息 |
| `AIMessagePromptTemplate` | 生成助手消息 |
| `PromptTemplate` | 基础文本模板 |
| `ChatPromptTemplate` | 按聊天顺序组合多条消息模板，一次交给 LLM |

须用 **`.from_template(...)`** 创建带花括号变量的模板，不要把裸字符串直接丢进错误构造方式。

导入：

```python
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    PromptTemplate,
    ChatPromptTemplate,
)
```

源码大致在：

```text
langchain-core/
└── prompts/
    ├── chat.py    → ChatPromptTemplate
    ├── base.py    → BasePromptTemplate
    ├── system.py  → SystemMessagePromptTemplate
    └── human.py   → HumanMessagePromptTemplate
```

架构对应：

```text
以前：System + Human → LLM → AI
现在：SystemMessagePromptTemplate + HumanMessagePromptTemplate
        →（填充）→ LLM → AIMessage
```

---

## 6. 实战：变量填充与 ChatPromptTemplate

### 6.1 定义单条模板

变量名与 notebook 一致：`school`、`topics`、`points`。

```python
system = SystemMessagePromptTemplate.from_template(
    "You are {school} teacher. You answer in short sentences."
)
question = HumanMessagePromptTemplate.from_template(
    "tell me about the {topics} in {points} points"
)
```

创建后可看 `input_variables`：human 侧为 `['points', 'topics']` 等。

### 6.2 单模板用 `.format()`（关键字参数）

单条 `*MessagePromptTemplate` **没有**适合整链的 `.invoke(dict)` 用法时，用 **`.format(...)`**：

```python
question.format(topics="sun", points=5)
# → HumanMessage(content='tell me about the sun in 5 points', ...)

system.format(school="elementary")
# → SystemMessage(content='You are elementary teacher. ...', ...)
```

### 6.3 组合成 ChatPromptTemplate 再用 `.invoke()`

```python
messages = [system, question]
template = ChatPromptTemplate(messages)
# 也常见：ChatPromptTemplate.from_messages([system, question])

prompt_value = template.invoke(
    {"school": "elementary", "topics": "sun", "points": 5}
)
response = llm.invoke(prompt_value)
print(response.content)
```

字典的**键必须与模板变量名一致**（写了 `{topics}` 就传 `"topics"`，不要混成 `topic`）。

### 6.4 结构示意

```text
ChatPromptTemplate
├── SystemMessagePromptTemplate
│   └── "You are {school} teacher..."
│   └── input_variables: ["school"]
├── HumanMessagePromptTemplate
│   └── "tell me about the {topics} in {points} points"
│   └── input_variables: ["topics", "points"]
└── invoke({school, topics, points}) → 消息列表 → llm.invoke(...)
```

### 6.5 运行时切换示例

| 变量 | 组合 A | 组合 B |
| --- | --- | --- |
| `school` | `elementary` | `phd` |
| `topics` | `sun` | `earth` |
| `points` | `5` | `3` |

只改字典，不必重写消息构造代码。LangSmith 里可看到填充后的 system/human 与最终 ChatOllama 调用。

### 6.6 `.format()` vs `.invoke()`

| API | 用在 | 作用 |
| --- | --- | --- |
| `.format(...)` | 单条 `*MessagePromptTemplate` | 填充 → 单条 Message（关键字参数） |
| `.invoke({...})` | `ChatPromptTemplate` | 填充全部变量 → 可交给 LLM 的 PromptValue / 消息序列 |

### 6.7 步骤小结

1. `from_template` 写带 `{占位符}` 的 System / Human 模板  
2. 单条可 `.format()`；组合后用 `ChatPromptTemplate.invoke({...})`  
3. 变量可来自不同消息（`school` 在系统侧，`topics` / `points` 在用户侧）  
4. 改一个变量即可切换角色或问题参数  

---

## 文末实践代码

```python
from dotenv import load_dotenv
import os
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)

load_dotenv("./../.env")
api_key = os.environ.get("LANGSMITH_API_KEY") or os.environ.get("LANGCHAIN_API_KEY")
print("API key loaded" if api_key else "No API key found")

base_url = "http://localhost:11434"
model = "qwen3"
llm = ChatOllama(base_url=base_url, model=model)

# --- 1) 纯字符串（默认人设）---
question = "tell me about the earth in 3 points"
print(llm.invoke(question).content)

# --- 2) 自定义角色模型（若本地已创建，可选）---
# print(ChatOllama(base_url=base_url, model="sherlock").invoke(question).content)
# print(ChatOllama(base_url=base_url, model="sheldon").invoke(question).content)

# --- 3) 运行时 SystemMessage / HumanMessage ---
messages = [
    SystemMessage("You are elementary teacher. You answer in short sentences."),
    HumanMessage("tell me about the earth in 3 points"),
]
print(llm.invoke(messages).content)

messages = [
    SystemMessage("You are phd teacher. You answer in short sentences."),
    HumanMessage("tell me about the earth in 3 points"),
]
print(llm.invoke(messages).content)

# --- 4) 提示模板 + ChatPromptTemplate ---
system = SystemMessagePromptTemplate.from_template(
    "You are {school} teacher. You answer in short sentences."
)
human = HumanMessagePromptTemplate.from_template(
    "tell me about the {topics} in {points} points"
)

print(system.format(school="elementary"))
print(human.format(topics="sun", points=5))

template = ChatPromptTemplate([system, human])
prompt = template.invoke(
    {"school": "elementary", "topics": "sun", "points": 5}
)
print(llm.invoke(prompt).content)
```
