---
title: Tool Calling
aliases:
  - Function Calling
  - 工具调用
  - bind_tools
created: 2026-07-27
updated: 2026-08-01
series: 本地 RAG
part: 11
source: Tool Calling.ipynb（可删）· 字幕 122–131（可删）
tags:
  - type/literature-note
  - topic/tool-calling
  - topic/langchain
  - topic/ollama
  - topic/agent
  - topic/tavily
  - topic/local-rag
  - status/draft
---

# Tool Calling（工具调用 / 函数调用）

> [!summary]
> **本地 RAG · 第 11 部分**。用 **`@tool` + `bind_tools`** 让 LLM 选型、填参；执行后经 **Human → AI(`tool_calls`) → ToolMessage → 最终 AIMessage** 闭环。两条路：自定义函数，或包装内置工具（Tavily / Wiki / PubMed / DDG）。这是后续 Agent 的底层形态。

默认：`ChatOllama(model="qwen3", base_url="http://localhost:11434")`  
工具文档：<https://python.langchain.com/docs/integrations/tools/>

## 本章目录

| 章节 | 学什么 |
| --- | --- |
| §1 概念 | 为何调工具；模型支持差异 |
| §2 自定义 `@tool` | docstring、invoke |
| §3 `bind_tools` | `tool_calls`、一句多问 |
| §4 内置搜索 | Tavily / DDG / Wiki / PubMed |
| §5 包装 + 选型 | `list_of_tools` |
| §6 完整一轮 | 消息闭环 |
| 文末实践代码 | 可复跑主路径 |

---

## 1. 概念

| 点 | 含义 |
| --- | --- |
| **自动调工具** | LLM 决定是否调、调哪个 |
| **自动填参** | 从自然语言抽出参数（如 `a=2, b=3`） |
| **Agent 必备** | 智能体几乎都依赖工具调用 |
| **并非人人支持** | 需支持 tool calling 的模型 |

课程口径：Llama / Qwen 等通常较好；Phi-3 系弱。约 3B 量级可能不稳，模型要够用。支持工具的 Chat 模型实现 **`.bind_tools()`**。

![[11-tool-cell2-0.png]]

```text
以前：Question → LLM → 直接文本（数学易幻觉）
现在：Question → LLM（已 bind 工具）
        → tool_calls（name + args）
        → 执行工具 → ToolMessage
        → 再交给 LLM → 最终答案
```

直觉：问「2×3」时，模型只负责认出 `multiply` 和参数，乘法由 Python 完成。电商场景同理：自然语言 → 抽出 `category / min_price / max_price` → 调库工具。

---

## 2. 自定义工具：`@tool`

```python
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.tools import tool

load_dotenv()
llm = ChatOllama(model="qwen3", base_url="http://localhost:11434")

@tool
def add(a, b):
    """
    Add two integer numbers together

    Args:
    a: First Integer
    b: Second Integer
    """
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """
    Multiply two integer numbers together

    Args:
    a: First Integer
    b: Second Integer
    """
    return int(a) * int(b)  # 模型常传字符串，强制转 int
```

| | 无 `@tool` | 有 `@tool` |
| --- | --- | --- |
| 类型 | 普通函数 | **StructuredTool**（Runnable） |
| 调用 | `add(1, 2)` | `add.invoke({"a": 1, "b": 2})` |
| 给 LLM | 无标准 schema | name / description / args |

Docstring 决定选型与填参质量——写清**何时用、参数含义**。可查看：

```python
add.name, add.description, add.args
add.args_schema.model_json_schema()  # 勿用已弃用的 .schema()
```

---

## 3. `bind_tools` 与 `tool_calls`

```python
tools = [add, multiply]
llm_with_tools = llm.bind_tools(tools)

ai = llm_with_tools.invoke("what is 1 plus 2?")
# ai.content 常为空
# ai.tool_calls → [{'name':'add','args':{'a':1,'b':2},'id':'...','type':'tool_call'}]
```

一句多问 → 多条 `tool_calls`，参数互不串：

```python
llm_with_tools.invoke(
    "what is 1 multiplied by 2, also what is 11 plus 22?"
).tool_calls
# multiply(1,2) + add(11,22)
```

此阶段只是「要调什么」，还不是最终自然语言答案。

---

## 4. 内置搜索工具

```bash
pip install -qU ddgs wikipedia xmltodict tavily-python
# 新版 Tavily 可迁：pip install langchain-tavily
```

| 工具 | Key | 场景 |
| --- | --- | --- |
| **Tavily** | `.env` 里 `TAVILY_API_KEY`（[tavily.com](https://tavily.com)，约 1000 次/月） | 实时新闻 / 股市 / 天气；正文质量较好 |
| **DuckDuckGo** | 免 key | 练手；多为 snippet |
| **Wikipedia** | 免 | 百科常识 |
| **PubMed** | 免 | 生物医学文献 |

改 `.env` 后须**重启 kernel 再 `load_dotenv()`**。`401 Unauthorized` → key 未加载或变量名不对。

```python
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun, TavilySearchResults
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools.pubmed.tool import PubmedQueryRun

DuckDuckGoSearchRun().invoke("What is today's stock market news?")

TavilySearchResults(
    max_results=5,
    search_depth="advanced",
    include_answer=True,
    include_raw_content=True,
).invoke("what is today's stock market news?")

WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()).invoke("What is LLM?")

PubmedQueryRun().invoke("What is the latest research on COVID-19?")
```

> [!note]
> `TavilySearchResults` 在部分版本已弃用，可改用 `langchain_tavily.TavilySearch`；课例仍用 community 类。

---

## 5. 包装内置工具 + 多工具选型

要让 LLM **自动选型**，把内置能力再包一层 `@tool`，description 写清场景：

```python
@tool
def wikipedia_search(query):
    """Search wikipedia for general information.

    Args:
    query: The search query
    """
    return WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()).invoke(query)

@tool
def pubmed_search(query):
    """Search pubmed for medical and life sciences queries.

    Args:
    query: The search query
    """
    return PubmedQueryRun().invoke(query)

@tool
def tavily_search(query):
    """Search the web for realtime and latest information.
    for examples, news, stock market, weather updates etc.

    Args:
    query: The search query
    """
    return TavilySearchResults(
        max_results=5,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True,
    ).invoke(query)

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integer numbers together

    Args:
    a: First Integer
    b: Second Integer
    """
    return int(a) * int(b)

tools = [wikipedia_search, pubmed_search, tavily_search, multiply]
list_of_tools = {t.name: t for t in tools}
llm_with_tools = llm.bind_tools(tools)
```

典型选型：新闻/股市 → `tavily_search`；肺癌治疗 → `pubmed_search`；`2 * 3` → `multiply`；「什么是 LLM」→ `wikipedia_search`。

---

## 6. 完整一轮：消息闭环

```text
messages = [HumanMessage]
  → llm_with_tools.invoke → AIMessage(tool_calls)
  → for 每个 tool_call：执行 → ToolMessage append
  → 再 invoke → AIMessage.content（最终回答）
```

| 坑 | 正确做法 |
| --- | --- |
| 只 append `tool_calls` | 必须 append **完整 AIMessage** |
| `tool.invoke(args)` | `selected_tool.invoke(tool_call)`（整条，含 id） |
| 多个 tool_call | **for 循环**逐个执行并 append |

```python
from langchain_core.messages import HumanMessage

query = "What is medicine for lung cancer?"
messages = [HumanMessage(query)]

ai_msg = llm_with_tools.invoke(messages)
messages.append(ai_msg)

for tool_call in ai_msg.tool_calls:
    name = tool_call["name"].lower()
    selected = list_of_tools[name]
    tool_msg = selected.invoke(tool_call)
    messages.append(tool_msg)

response = llm_with_tools.invoke(messages)
print(response.content)
```

Agent 框架会自动跑这套闭环；本课手写是为了看清底层。

---

## 文末实践代码

```python
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_community.tools import WikipediaQueryRun, TavilySearchResults
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools.pubmed.tool import PubmedQueryRun

load_dotenv()
llm = ChatOllama(model="qwen3", base_url="http://localhost:11434")


@tool
def wikipedia_search(query):
    """Search wikipedia for general information.

    Args:
    query: The search query
    """
    return WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()).invoke(query)


@tool
def pubmed_search(query):
    """Search pubmed for medical and life sciences queries.

    Args:
    query: The search query
    """
    return PubmedQueryRun().invoke(query)


@tool
def tavily_search(query):
    """Search the web for realtime and latest information.
    for examples, news, stock market, weather updates etc.

    Args:
    query: The search query
    """
    return TavilySearchResults(
        max_results=5,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True,
    ).invoke(query)


@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integer numbers together

    Args:
    a: First Integer
    b: Second Integer
    """
    return int(a) * int(b)


tools = [wikipedia_search, pubmed_search, tavily_search, multiply]
list_of_tools = {t.name: t for t in tools}
llm_with_tools = llm.bind_tools(tools)

# --- 只看选型 ---
print(llm_with_tools.invoke("what is 2 * 3?").tool_calls)

# --- 完整闭环 ---
query = "What is medicine for lung cancer?"
messages = [HumanMessage(query)]
ai_msg = llm_with_tools.invoke(messages)
messages.append(ai_msg)

for tool_call in ai_msg.tool_calls:
    selected = list_of_tools[tool_call["name"].lower()]
    messages.append(selected.invoke(tool_call))

print(llm_with_tools.invoke(messages).content)
```
