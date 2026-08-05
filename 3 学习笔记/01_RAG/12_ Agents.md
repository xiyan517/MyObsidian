---
title: Agents
aliases:
  - LangChain Agents
  - create_agent
  - Agentic RAG
  - 智能体
created: 2026-07-27
updated: 2026-08-01
series: 本地 RAG
part: 12
source: Agents.ipynb · tools.py · Agentic RAG.ipynb（可删）· 字幕 132–148（可删）
tags:
  - type/literature-note
  - topic/agent
  - topic/agentic-rag
  - topic/langchain
  - topic/langgraph
  - topic/ollama
  - topic/faiss
  - topic/local-rag
  - status/draft
---

# Agents + Agentic RAG（LangChain v1）

> [!summary]
> **本地 RAG · 第 12 部分**。上半：用 **`create_agent`** 把 LLM + Tools + System Prompt 收成可 `invoke` / `stream` 的 Agent（含 middleware 动态选模型）。下半：**Agentic RAG**——把 FAISS 检索做成 `@tool`，由 Agent 决定是否/如何检索并带引用作答。接 Tool Calling 手工闭环；本课由框架自动跑消息循环。

默认：`ChatOllama(model="qwen3", base_url="http://localhost:11434")`  
入口：`from langchain.agents import create_agent`  
文档：<https://docs.langchain.com>

## 本章目录

| 章节 | 学什么 |
| --- | --- |
| §1 Agent 概念与前置 | v1 API、三大组件 |
| §2 `web_search` 工具 | `tools.py` / DDGS |
| §3 静态 Agent | `create_agent`、state、调参 |
| §4 Middleware 动态选型 | `@wrap_model_call` |
| §5 流式 | `values` / `updates` / `messages` |
| §6 Agentic RAG 概念 | vs 普通 RAG |
| §7 检索工具 + Agent | `retrieve_context`、引用 |
| §8 流式测试 | `ask` / 是否调工具 |
| 文末实践代码 | Agent + Agentic RAG 骨架 |

---

## 1. Agent 概念与前置

| 组件 | 作用 |
| --- | --- |
| **LLM** | 推理、是否调工具 |
| **Tools** | 搜索、检索、API… |
| **System Prompt** | 行为边界 |

```text
Query → LLM →（需要时）Tool → Observation → LLM → … → 最终答案
```

v1 用 `langchain.agents.create_agent`（底层仍是 LangGraph）；旧 `create_react_agent` 步骤更繁。

```bash
pip install -U langchain langchain-community langchain-core langgraph
pip install -U ddgs python-dotenv faiss-cpu
ollama pull qwen3
# 动态选型课例另用 llama3.2；Agentic RAG 还需：
ollama pull nomic-embed-text
```

---

## 2. 工具：`tools.py`（DuckDuckGo）

```python
# tools.py（课例摘要）
from dotenv import load_dotenv
load_dotenv()
from langchain_core.tools import tool
from ddgs import DDGS

@tool
def web_search(query: str, num_results: int = 10) -> str:
    """Search the web using DuckDuckGo.

    Args:
        query: Search query string
        num_results: Number of results to return (default: 10)
    """
    results = list(
        DDGS().text(
            query=query,
            max_results=num_results,
            region="us-en",
            timelimit="d",
            backend="google, bing, brave, yahoo, wikipedia, duckduckgo",
        )
    )
    # 格式化为 title / body / href 字符串返回
    ...
```

Docstring 决定 LLM 何时调用。可先 `tools.web_search.invoke({"query": "...", "num_results": 1})` 单测。

---

## 3. 静态 Agent：`create_agent`

```python
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
import tools

system_prompt = """You are a helpful AI assistant.
Use the available tools when needed to answer questions accurately.
If you need to search for information, use the web_search tool.
Always provide clear and concise answers.
"""

model = ChatOllama(model="qwen3", base_url="http://localhost:11434")
agent = create_agent(
    model=model,
    tools=[tools.web_search],
    system_prompt=system_prompt,
)

result = agent.invoke({"messages": "What is the top 10 global news right now?"})
# result["messages"]：Human → AI(tool_calls) → Tool → AI(最终)
print(result["messages"][-1].content)
# result["messages"][-1].pretty_print()
```

| 点 | 说明 |
| --- | --- |
| 输入 | `{"messages": ...}`；字符串可自动变 HumanMessage |
| 输出 | 完整 state；默认关键键 `messages` |
| 多轮 | `agent.invoke(result)` 把上一轮 state 接着传 |

### 调参试验

```python
model1 = ChatOllama(
    model="qwen3",
    base_url="http://localhost:11434",
    temperature=0,
    top_p=1,
    # notebook 里写成 repeart_penalty，正确参数名多为 repeat_penalty
    repeat_penalty=1.2,
    num_predict=1000,
    num_ctx=4096,
    reasoning=True,  # 支持思考的模型才有用
)
```

| 参数 | 作用 |
| --- | --- |
| `temperature` | 随机性 |
| `num_predict` | 最大生成长度 |
| `num_ctx` | 上下文窗 |
| `top_p` / `repeat_penalty` | 采样与去重 |
| `reasoning` | 推理链（看 `additional_kwargs`） |

---

## 4. Middleware：运行时动态选模型

静态 = 创建时焊死一个 LLM。动态 = `@wrap_model_call` 在请求到达模型前改 `request.model`。

课例逻辑（notebook）：消息数 **&lt; 3 → Qwen3**；**≥ 3 → llama3.2**（markdown 曾写 Gemma3，但视觉模型不宜绑工具，实码用 llama3.2）。

```python
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse

basic_model = ChatOllama(model="qwen3", base_url="http://localhost:11434", num_predict=1000)
advanced_model = ChatOllama(model="llama3.2", base_url="http://localhost:11434", num_predict=1000)

@wrap_model_call
def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:
    message_count = len(request.state["messages"])
    if message_count < 3:
        print(f"Using Qwen3 for {message_count} messages")
        request.model = basic_model
    else:
        print(f"Using llama3.2 for {message_count} messages")
        request.model = advanced_model
    return handler(request)

agent = create_agent(
    model=basic_model,
    tools=[tools.web_search],
    system_prompt=system_prompt,
    middleware=[dynamic_model_selection],
)

def get_agent_output(messages: list):
    return agent.invoke({"messages": messages})

messages = ["How are you?", "What's the weather in Mumbai today?"]
result = get_agent_output(messages)
# 典型日志：先 Qwen3(2 msgs) → 调工具后 4 msgs → llama3.2
```

客服 / 研究助手等：简单问小模型，复杂或轮次多再切大模型。

---

## 5. 流式：`agent.stream`

| `stream_mode` | 内容 |
| --- | --- |
| **`values`** | 每步完整 state（常用） |
| **`updates`** | 仅增量：`model` / `tools` |
| **`messages`** | 偏消息侧更新 |

```python
for chunk in agent.stream({"messages": messages}, stream_mode="values"):
    print(chunk["messages"][-1].content, end="", flush=True)
    print("\n\n------")

for chunk in agent.stream({"messages": messages}, stream_mode="updates"):
    if "model" in chunk:
        chunk["model"]["messages"][-1].pretty_print()
    if "tools" in chunk:
        chunk["tools"]["messages"][-1].pretty_print()
```

---

## 6. Agentic RAG：与普通 RAG 的差别

| | 普通 RAG（§10） | Agentic RAG |
| --- | --- | --- |
| 流程 | 每问必检索 → 再生成 | 问题先进 Agent，**自行决定**是否检索 |
| 查询 | 用户原句进向量库 | LLM 可**改写**传给工具的 query |
| 失败 | 一次检索完事 | 可换 query 再查（进阶变体） |
| 架构 | Retrieve → Generate 直线 | LLM ↔ `retrieve_context` Tool 循环 |

```text
普通：Question → Embed → Search → chunks + Q → LLM
Agentic：Question → Agent(LLM)
              ↕ 按需
         retrieve_context @tool → FAISS
              → 带引用的最终答案
```

Self-RAG / Corrective RAG 等是在此块上的延伸；本课搭基础版。

---

## 7. 向量库 + `retrieve_context` + `create_agent`

前置：§9 已 `save_local` 的库（课例 `health_supplements`，约 311 条）。

```python
import os, warnings
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import FAISS

os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
warnings.filterwarnings("ignore")
load_dotenv()

llm = ChatOllama(model="qwen3", base_url="http://localhost:11434")
embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url="http://localhost:11434")

vector_store = FAISS.load_local(
    "./../09. Vector Stores and Retrievals/health_supplements",
    embeddings,
    allow_dangerous_deserialization=True,
)
# vector_store.index.ntotal → 311

@tool()
def retrieve_context(query: str):
    """Retrieve relevant information for health related queries from the document to answer the query.
    """
    print(f"Searching: '{query}'")
    docs = vector_store.similarity_search(query, k=4)
    content = "\n\n".join(
        f"Source: {doc.metadata.get('source', '?')} (Page {doc.metadata.get('page', '?')}): {doc.page_content}"
        for doc in docs
    )
    print(f"Found {len(docs)} relevant chunks")
    return content

tools = [retrieve_context]
system_prompt = """You are a research assistant with a document retrieval tool.

Tool:
- retrieve_context: Search the document for the health related question

Cite page numbers and reference document while writing the answer and be thorough."""

rag_agent = create_agent(llm, tools, system_prompt=system_prompt)

result = rag_agent.invoke({"messages": "What is the use of BCAA?"})
result["messages"][-1].pretty_print()
# 工具侧常见：LLM 改写 query 为 "use of BCAA" 再检索
```

| 点 | 说明 |
| --- | --- |
| Embedding | 必须与入库一致 |
| 返回格式 | Source + Page + content → 便于引用 |
| System | 要求 cite；**不要**写死「永远必须调工具」——通用问题可直答 |

---

## 8. Agentic RAG 流式测试

```python
def ask(question: str):
    print(f"\n{'='*60}\nQuestion: {question}\n{'='*60}")
    for event in rag_agent.stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="values",
    ):
        msg = event["messages"][-1]
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                print(f"Tool: {tc['name']} | {tc['args']}")
        elif hasattr(msg, "content") and msg.content:
            print(f"\nAnswer:\n{msg.content}")

ask("how to gain muscle mass?")       # 通常会调 retrieve_context
ask("tell me 3 facts about Earth?")   # 通常不调工具，直接答
```

可再包一层 `while True` + `input()` 做交互聊天（`quit` / `exit` / `q` 退出）。Markdown Viewer 看引用格式更清晰。

---

## 对照速查

| 概念 | API / 位置 |
| --- | --- |
| 创建 Agent | `create_agent(model, tools, system_prompt=..., middleware=...)` |
| 联网工具 | `tools.web_search`（DDGS） |
| 动态模型 | `@wrap_model_call` 改 `request.model` |
| 流式 | `stream_mode="values"\|"updates"\|"messages"` |
| 普通 RAG | 每问必检索（§10 LCEL 链） |
| Agentic RAG | 检索是 Tool，Agent 按需调用 |
| 文档工具 | `retrieve_context` → FAISS `similarity_search` |

---

## 文末实践代码

### A. Web Search Agent

```python
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
import tools  # 同目录 tools.py

system_prompt = """You are a helpful AI assistant.
Use the available tools when needed. Prefer web_search for current facts."""

agent = create_agent(
    model=ChatOllama(model="qwen3", base_url="http://localhost:11434"),
    tools=[tools.web_search],
    system_prompt=system_prompt,
)

result = agent.invoke({"messages": "What is the top global news right now?"})
print(result["messages"][-1].content)
```

### B. Agentic RAG（检索工具）

```python
import os, warnings
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import FAISS

os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
warnings.filterwarnings("ignore")
load_dotenv()

llm = ChatOllama(model="qwen3", base_url="http://localhost:11434")
embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url="http://localhost:11434")
vector_store = FAISS.load_local(
    "./../09. Vector Stores and Retrievals/health_supplements",
    embeddings,
    allow_dangerous_deserialization=True,
)

@tool()
def retrieve_context(query: str):
    """Retrieve relevant information for health related queries from the document to answer the query.
    """
    docs = vector_store.similarity_search(query, k=4)
    return "\n\n".join(
        f"Source: {doc.metadata.get('source', '?')} (Page {doc.metadata.get('page', '?')}): {doc.page_content}"
        for doc in docs
    )

rag_agent = create_agent(
    llm,
    [retrieve_context],
    system_prompt="""You are a research assistant with a document retrieval tool.
Tool: retrieve_context for health related questions.
Cite page numbers and reference documents. Be thorough.""",
)

for event in rag_agent.stream(
    {"messages": [{"role": "user", "content": "What is the use of BCAA?"}]},
    stream_mode="values",
):
    msg = event["messages"][-1]
    if getattr(msg, "tool_calls", None):
        print("tool_calls:", msg.tool_calls)
    elif getattr(msg, "content", None):
        print(msg.content)
```
