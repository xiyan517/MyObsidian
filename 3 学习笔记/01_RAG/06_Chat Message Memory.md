---
title: Chat Message Memory
aliases:
  - 聊天记忆
  - RunnableWithMessageHistory
  - SQLChatMessageHistory
  - MessagesPlaceholder
created: 2026-08-01
updated: 2026-08-01
series: 本地 RAG
part: 6
source: Chat Message Memory.ipynb（可删）· 字幕 062–066（可删）
tags:
  - type/literature-note
  - topic/langchain
  - topic/memory
  - topic/ollama
  - topic/local-rag
  - status/draft
---

# Chat Message Memory（会话消息记忆）

> [!summary]
> **本地 RAG · 第 6 部分**。用 **`RunnableWithMessageHistory`** 包住链：按 **`session_id`** 在调用前加载历史、调用后写入回复。持久化用 **`SQLChatMessageHistory`（SQLite）**；推荐 Prompt 里放 **`MessagesPlaceholder("history")`**，配合 `input_messages_key` / `history_messages_key`。

默认：`ChatOllama(base_url="http://localhost:11434", model="qwen3")`。

## 本章目录

| 章节 | 学什么 |
| --- | --- |
| §1 为什么要记忆 | session_id；加载 → 调用 → 保存 |
| §2 无记忆基线 | 第二次问名字会失败 |
| §3 SQL + RunnableWithMessageHistory | 存库、config、`HumanMessage` 调用 |
| §4 MessagesPlaceholder（推荐） | System + history + `{input}` |
| 文末实践代码 | 可复跑主路径 |

---

## 1. 为什么要记忆

无记忆时，每次 `chain.invoke` 都是新会话：上一轮说过的名字、角色设定，下一轮模型**不记得**。

有记忆后：用 **`session_id`**（可当 user_id）区分多路对话；同一 id 下多轮共享历史（类似 ChatGPT 一个聊天窗口）。

`RunnableWithMessageHistory` 包住另一条 Runnable，做两件事：

1. **调用前**：按 `session_id` 加载历史消息，拼进输入  
2. **调用后**：把本轮 human / AI 消息写回存储  

![[06-chat-memory-cell2-0.png]]

```text
用户输入 + session_id（在 config 里）
  → Get History（按 session_id）
  → Chain（Prompt → LLM → Parser）
  → Save Response
  → 返回输出
```

调用时必须在 config 里带上：

```python
config = {"configurable": {"session_id": "某个会话名"}}
```

搭建时要想清两件事：**历史存在哪、怎么读**；以及**被包裹的链输入/输出长什么样**。

---

## 2. 无记忆基线：问题复现

先搭一条最简单的链，验证「第二次提问不记得第一次」：

```python
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv("./../.env")

llm = ChatOllama(base_url="http://localhost:11434", model="qwen3")

template = ChatPromptTemplate.from_template("{prompt}")
chain = template | llm | StrOutputParser()

about = "My name is Laxmi Kant. I work for KGP Talkie."
print(chain.invoke({"prompt": about}))
# 能回应自我介绍

print(chain.invoke({"prompt": "What is my name?"}))
# 典型结果：不知道你的名字 —— 两次 invoke 互不相干
```

本阶段 Prompt 可以只有 `{prompt}` / `{input}`；有 history 之后，角色也可放在首轮 human 里，或单独写 System（§4）。

---

## 3. `SQLChatMessageHistory` + `RunnableWithMessageHistory`

### 3.1 存哪里

用 SQLite 持久化，按 `session_id` 读写：

```python
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory

def get_session_history(session_id):
    return SQLChatMessageHistory(
        session_id,
        connection="sqlite:///chat_history.db",  # 连接串，不要只写裸文件名
    )
```

历史里主要是 **`HumanMessage` + `AIMessage`**。可查看 / 清空：

```python
user_id = "laxmi_kant"
history = get_session_history(user_id)
history.get_messages()  # 或 .messages（视版本）
history.clear()
```

### 3.2 包住链

```python
runnable_with_history = RunnableWithMessageHistory(chain, get_session_history)
```

包装后本身仍是 Runnable，可 `.invoke(...)`。

### 3.3 用消息列表 + config 调用

Notebook 第一种写法：输入是 **`HumanMessage` 列表**，config 带 `session_id`：

```python
user_id = "laxmi_kant"
about = "My name is Laxmi Kant. I work for KGP Talkie."

runnable_with_history.invoke(
    [HumanMessage(content=about)],
    config={"configurable": {"session_id": user_id}},
)

runnable_with_history.invoke(
    [HumanMessage(content="whats my name?")],
    config={"configurable": {"session_id": user_id}},
)
# 应能答出 Laxmi Kant
```

| 点 | 说明 |
| --- | --- |
| `session_id` | 换一个 id = 新会话，互不串味 |
| 小模型 | 记忆/指令遵循可能不稳，必要时换更大模型 |
| LangSmith | 可看到 load history 等步骤 |

> [!note]
> 直接把字符串塞进「未预留 history 槽位」的简单模板时，历史注入有时不稳。下一节用 **`MessagesPlaceholder`**，这是推荐写法。

---

## 4. 推荐：`MessagesPlaceholder` + 字典输入

### 4.1 Prompt 顺序

```text
SystemMessage（固定助手设定）
MessagesPlaceholder("history")  ← 框架自动填入历史
HumanMessage（当前 {input}）
```

```python
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
    MessagesPlaceholder,
)

system = SystemMessagePromptTemplate.from_template("You are helpful assistant.")
human = HumanMessagePromptTemplate.from_template("{input}")

prompt = ChatPromptTemplate(
    messages=[system, MessagesPlaceholder(variable_name="history"), human]
)

chain = prompt | llm | StrOutputParser()

runnable_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",      # invoke 字典里当前问题的键
    history_messages_key="history",  # 对应 MessagesPlaceholder 变量名
)
```

| 参数 | 作用 |
| --- | --- |
| `input_messages_key="input"` | `invoke({"input": "..."})` 的当前轮 |
| `history_messages_key="history"` | 与 `MessagesPlaceholder("history")` 对齐；**不用手传 history** |

### 4.2 封装调用

```python
def chat_with_llm(session_id, input):
    return runnable_with_history.invoke(
        {"input": input},
        config={"configurable": {"session_id": session_id}},
    )

user_id = "kgptalkie"
print(chat_with_llm(user_id, about))
print(chat_with_llm(user_id, "what is my name?"))  # 能回忆
```

换新 `session_id` → 新会话；同一 id → 连续多轮。

```text
invoke({"input": ...}, config={session_id})
  → 按 session_id 读 SQLite
  → 填入 MessagesPlaceholder("history")
  → System + 历史 + 当前 Human → LLM → str
  → 本轮消息写回 SQLite
```

后续做 Streamlit 聊天机器人时，核心就是这一套：`session_id` + `SQLChatMessageHistory` + `MessagesPlaceholder` + `RunnableWithMessageHistory`（页面气泡另用前端 state，与库内记忆分开管）。

---

## 要点速查

| 项 | 记法 |
| --- | --- |
| 无记忆 | 每次 `invoke` 独立，问名字会失败 |
| 存储 | `SQLChatMessageHistory(session_id, connection="sqlite:///….db")` |
| 包装 | `RunnableWithMessageHistory(chain, get_session_history, …)` |
| 配置 | `config={"configurable": {"session_id": "..."}}` |
| 推荐 Prompt | System → `MessagesPlaceholder("history")` → Human `{input}` |
| 键名 | `input_messages_key="input"`，`history_messages_key="history"` |
| 清空 | `get_session_history(id).clear()` |

---

## 文末实践代码

```python
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory

load_dotenv("./../.env")

llm = ChatOllama(base_url="http://localhost:11434", model="qwen3")


def get_session_history(session_id):
    return SQLChatMessageHistory(
        session_id,
        connection="sqlite:///chat_history.db",
    )


# --- A) 无记忆：第二次通常答不出名字 ---
bare = ChatPromptTemplate.from_template("{prompt}") | llm | StrOutputParser()
about = "My name is Laxmi Kant. I work for KGP Talkie."
print(bare.invoke({"prompt": about}))
print(bare.invoke({"prompt": "What is my name?"}))

# --- B) 有记忆 + MessagesPlaceholder（推荐）---
system = SystemMessagePromptTemplate.from_template("You are helpful assistant.")
human = HumanMessagePromptTemplate.from_template("{input}")
prompt = ChatPromptTemplate(
    messages=[system, MessagesPlaceholder(variable_name="history"), human]
)
chain = prompt | llm | StrOutputParser()

runnable_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)


def chat_with_llm(session_id, user_input):
    return runnable_with_history.invoke(
        {"input": user_input},
        config={"configurable": {"session_id": session_id}},
    )


user_id = "kgptalkie"
get_session_history(user_id).clear()  # 演示前清空该会话

print(chat_with_llm(user_id, about))
print(chat_with_llm(user_id, "what is my name?"))
print(get_session_history(user_id).get_messages())

# --- C) 可选：消息列表写法（简单 chain 时）---
# simple = ChatPromptTemplate.from_template("{prompt}") | llm | StrOutputParser()
# rwh = RunnableWithMessageHistory(simple, get_session_history)
# rwh.invoke(
#     [HumanMessage(content=about)],
#     config={"configurable": {"session_id": "laxmi_kant"}},
# )
```
