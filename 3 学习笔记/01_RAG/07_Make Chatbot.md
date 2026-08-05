---
title: Make Chatbot
aliases:
  - 构建聊天机器人
  - Streamlit Chatbot
  - chat_stream
created: 2026-07-25
updated: 2026-08-01
series: 本地 RAG
part: 7
source: chat_stream.py（可删）· 字幕 067–074（可删）
tags:
  - type/literature-note
  - topic/streamlit
  - topic/langchain
  - topic/ollama
  - topic/local-rag
  - status/draft
---

# Make Chatbot（Streamlit 本地聊天）

> [!summary]
> **本地 RAG · 第 7 部分**。用 **Streamlit** 做 UI，**ChatOllama + LCEL + `RunnableWithMessageHistory`** 做多轮记忆（SQLite）。页面气泡靠 `st.session_state`；模型上下文靠 `SQLChatMessageHistory`。回复推荐 **`stream` + `st.write_stream`**（也可改 `invoke`）。

默认：`ChatOllama(base_url="http://localhost:11434", model="qwen3")`。Streamlit 入门可参考官方文档与课内 playlist：<https://www.youtube.com/watch?v=hff2tHUzxJM&list=PLc2rvfiptPSSpZ99EnJbH5LjTJ_nOoSWW>

## 本章目录

| 章节 | 学什么 |
| --- | --- |
| §1 要做什么 | 功能表、双存储、数据流 |
| §2 Streamlit 骨架 | title、session_state、chat_input / chat_message |
| §3 接上记忆链 | MessagesPlaceholder + RunnableWithMessageHistory |
| §4 一轮对话 | 写 UI 历史 → 调 LLM → 写 assistant |
| §5 流式 vs 普通 | `stream`/`write_stream` 与 `invoke`/`markdown` |
| §6 编写顺序与启动 | 建议步骤、`streamlit run` |
| 文末完整代码 | 与 `chat_stream.py` 对齐（流式） |

---

## 1. 要做什么

类 ChatGPT 的**本地**聊天页：多轮上下文、按用户 id 隔离会话、可清空、可选流式吐字。

| 功能 | 做什么 |
| --- | --- |
| 本地聊天 | Ollama 本机模型（课例 `qwen3`，也可换已 pull 的其它名） |
| 用户 ID | `st.text_input` → 当作 `session_id` |
| 多轮记忆 | `SQLChatMessageHistory` → `sqlite:///chat_history.db` |
| 流式回复 | `stream` + `st.write_stream` |
| 普通回复 | `invoke` + `st.markdown`（二选一，勿并存） |
| 新对话 | 清空页面列表 + `get_session_history(user_id).clear()` |
| 页面气泡 | `st.session_state.chat_history` 只负责**当前页展示** |

**双存储（务必分清）**

| 存储 | 存什么 | 谁读 |
| --- | --- | --- |
| `st.session_state.chat_history` | UI 气泡 `[{role, content}, …]` | Streamlit 渲染 |
| SQLite（`SQLChatMessageHistory`） | LangChain 消息历史 | `RunnableWithMessageHistory` |

关浏览器后 `session_state` 常丢；同一 `user_id` 下 SQLite 仍可保留模型上下文。新对话必须**两边都清**，否则页面空了模型仍记得旧话。

```text
用户输入 (st.chat_input)
  → append user 到 session_state，并即时 chat_message 显示
  → runnable_with_history（按 user_id 读/写 SQLite）
       ├─ stream  → st.write_stream
       └─ invoke  → st.markdown
  → append 完整 assistant 到 session_state
  → 下次 rerun：for 循环重绘全部气泡
```

> [!warning]
> 私有数据调试时慎用 LangSmith（会上传 trace）；可去掉相关环境变量，或改用 Langfuse 等自托管方案。

> [!warning]
> `chat_with_llm` 的流式版与普通版、以及两段 `if prompt:` **不要同时保留**——同名函数后者覆盖前者；两段 `if` 会把同一条消息处理两遍。

---

## 2. Streamlit 页面骨架

安装与启动：

```bash
pip install streamlit
streamlit run chat_stream.py
```

界面大致：**标题/说明 → user id →「新对话」按钮 → 气泡区 → 底部 `st.chat_input`**。

```python
import streamlit as st

st.title("Make Your Own Chatbot")
st.write("Chat with me!")

user_id = st.text_input("Enter your user id", "laxmikant")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if st.button("Start New Conversation"):
    st.session_state.chat_history = []
    get_session_history(user_id).clear()  # 见 §3；须同时清 SQLite

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("What is up?")
```

| API | 作用 |
| --- | --- |
| `st.session_state` | 跨 rerun 保留页面变量 |
| `st.chat_input` | 底部聊天输入；有值才触发本轮 |
| `st.chat_message("user"\|"assistant")` | 聊天气泡容器 |
| `st.markdown` / `st.write_stream` | 显示文本 / 流式文本 |

Streamlit 每次交互会**重跑脚本**。当轮输入若只 `append` 到列表、不在当次用 `st.chat_message` 画出来，可能要等下一次交互才出现在顶部循环里——所以当前轮要**即时画** user / assistant。

---

## 3. 接上记忆链（来自 Chat Message Memory）

核心与第 6 部分相同：System + `MessagesPlaceholder("history")` + Human `{input}`，再包 `RunnableWithMessageHistory`。

```python
from langchain_ollama import ChatOllama
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory

base_url = "http://localhost:11434"
model = "qwen3"
db_connection = "sqlite:///chat_history.db"  # 连接串，不要只写裸文件名


def get_session_history(session_id):
    return SQLChatMessageHistory(session_id, connection=db_connection)


llm = ChatOllama(base_url=base_url, model=model)

system = SystemMessagePromptTemplate.from_template("You are helpful assistant.")
human = HumanMessagePromptTemplate.from_template("{input}")
prompt_template = ChatPromptTemplate(
    messages=[system, MessagesPlaceholder(variable_name="history"), human]
)
chain = prompt_template | llm | StrOutputParser()

runnable_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)
```

`user_id` = `config` 里的 `session_id`：同一 id 共享 SQLite 记忆；换 id = 新会话。演示：先说「我是小学生，请用三点、简短回答」，再问太阳/地球，风格会沿用——这就是记忆链的价值。

---

## 4. 一轮对话：更新 UI + 调 LLM

```text
if prompt:
  1. append {role:user, content:prompt}
  2. 即时 st.chat_message("user") 显示
  3. 调 chat_with_llm(user_id, prompt)
  4. 即时显示 assistant
  5. append {role:assistant, content:完整回复}
```

普通（`invoke`）版示意：

```python
def chat_with_llm(session_id, input_text):
    return runnable_with_history.invoke(
        {"input": input_text},
        config={"configurable": {"session_id": session_id}},
    )


if prompt:
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        response = chat_with_llm(user_id, prompt)
        st.markdown(response)
    st.session_state.chat_history.append({"role": "assistant", "content": response})
```

`invoke` 会等整段生成完才出现——下一节改流式。

---

## 5. 流式输出（推荐，对齐 `chat_stream.py`）

把 `invoke` 改成生成器 + `stream`，UI 用 `st.write_stream`：

```python
def chat_with_llm(session_id, input_text):
    for output in runnable_with_history.stream(
        {"input": input_text},
        config={"configurable": {"session_id": session_id}},
    ):
        yield output


if prompt:
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        response = st.write_stream(chat_with_llm(user_id, prompt))
    st.session_state.chat_history.append({"role": "assistant", "content": response})
```

| 对比 | 流式 | 普通 |
| --- | --- | --- |
| 方法 | `.stream` + `yield` | `.invoke` + `return` |
| UI | `st.write_stream(...)` | `st.markdown(response)` |
| 体验 | 边生成边显示 | 等完再显示 |

`st.write_stream` 结束后返回**完整字符串**，再写入 `session_state` 的 assistant 条目，供下次 rerun 重绘。

---

## 6. 编写顺序与启动

建议按课序搭：

1. 导入 Streamlit / ChatOllama / 提示模板（含 **`MessagesPlaceholder`**）/ 记忆与 `StrOutputParser`  
2. 标题、`base_url`、`model`、`db_connection`  
3. `user_id = st.text_input(...)`  
4. `get_session_history`  
5. 初始化 `chat_history` +「Start New Conversation」（清 UI + `clear()`）  
6. `for` 渲染已有气泡  
7. 搭链并包 `RunnableWithMessageHistory`  
8. 写 `chat_with_llm`（**只留** stream 或 invoke）  
9. `st.chat_input` + 对应的一段 `if prompt:`  
10. 启动：

```bash
streamlit run chat_stream.py
```

| 常见坑 | 处理 |
| --- | --- |
| 未导入 `MessagesPlaceholder` | 加入 prompts 导入 |
| `connection='chat_history.db'` | 改为 `sqlite:///chat_history.db` |
| 两套 `chat_with_llm` / 两个 `if prompt` | 只留配套的一套 |
| 只清 UI 不清 SQLite | 新对话仍带旧上下文 |
| 从别的文件 `import base_url` | 本文件内定义即可 |

---

## 文末完整代码（流式，对齐课程 `chat_stream.py`）

```python
# Streamlit playlist:
# https://www.youtube.com/watch?v=hff2tHUzxJM&list=PLc2rvfiptPSSpZ99EnJbH5LjTJ_nOoSWW

import streamlit as st
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.output_parsers import StrOutputParser

load_dotenv("./../.env")

st.title("Make Your Own Chatbot")
st.write("Chat with me!")

base_url = "http://localhost:11434"
model = "qwen3"
db_connection = "sqlite:///chat_history.db"

user_id = st.text_input("Enter your user id", "laxmikant")


def get_session_history(session_id):
    return SQLChatMessageHistory(session_id, connection=db_connection)


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if st.button("Start New Conversation"):
    st.session_state.chat_history = []
    get_session_history(user_id).clear()

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

llm = ChatOllama(base_url=base_url, model=model)

system = SystemMessagePromptTemplate.from_template("You are helpful assistant.")
human = HumanMessagePromptTemplate.from_template("{input}")
prompt_template = ChatPromptTemplate(
    messages=[system, MessagesPlaceholder(variable_name="history"), human]
)
chain = prompt_template | llm | StrOutputParser()

runnable_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)


def chat_with_llm(session_id, input_text):
    for output in runnable_with_history.stream(
        {"input": input_text},
        config={"configurable": {"session_id": session_id}},
    ):
        yield output


prompt = st.chat_input("What is up?")

if prompt:
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        response = st.write_stream(chat_with_llm(user_id, prompt))
    st.session_state.chat_history.append({"role": "assistant", "content": response})
```

### 若改用普通 `invoke`

只替换函数与 `if prompt:` 中 assistant 那一段：

```python
def chat_with_llm(session_id, input_text):
    return runnable_with_history.invoke(
        {"input": input_text},
        config={"configurable": {"session_id": session_id}},
    )


# if prompt 内 assistant 部分改为：
# with st.chat_message("assistant"):
#     response = chat_with_llm(user_id, prompt)
#     st.markdown(response)
```
