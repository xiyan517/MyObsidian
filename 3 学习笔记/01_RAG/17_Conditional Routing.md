---
title: Conditional Routing
aliases:
  - LangGraph 条件路由
  - add_conditional_edges
  - Structured Output 路由
  - 17 Conditional Routing
created: 2026-08-09
updated: 2026-08-09
series: 本地 RAG
part: 17
source: Conditional Routing.ipynb（可删）· LLM Integration & Routing with Structured Output · [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph/overview)
tags:
  - type/literature-note
  - topic/langgraph
  - topic/langchain
  - topic/conditional-routing
  - topic/structured-output
  - topic/local-rag
  - status/draft
---

# Conditional Routing（结构化输出 + 条件边）

> [!summary]
> **本地 RAG · 第 17 部分**。在 [[16_LangGraph]] 的线性图之上：用 **`with_structured_output`** 让节点产出可分支的字段（情感 / 置信度），再用 **`add_conditional_edges`** 按路由函数跳到不同回复节点。对应官方定位里「**同一张图混用确定性步骤与 LLM 驱动步骤**」：路由函数是确定性的，分析 / 回复节点是 agentic 的。课例是 **Twitter 客服 Agent**。

前置：[[16_LangGraph]] · 结构化输出对照：[[05_Output Parsing]] · LCEL 路由对照：[[04_Chains]] · 环境：[[杂项]]

主要链接：

- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) — 编排定位与核心能力
- [Graph API · Conditional edges](https://docs.langchain.com/oss/python/langgraph/graph-api#conditional-edges) — `add_conditional_edges` 语义
- Notebook：`临时文件/Conditional Routing.ipynb`（可删）· 课程频道：KGP Talkie

## 本章目录

| 章节 | 学什么 |
| --- | --- |
| §1 定位 | 官方编排观；确定性 vs agentic；条件分叉；对照 LCEL |
| §2 场景与目标 | Twitter 客服；学习目标与落地场景 |
| §3 模型与 Schema | `ChatOllama`；`SentimentAnalysis` Pydantic |
| §4 State | `SentimentState`：输入 / 分析结果 / 回复 |
| §5 节点 | `analyze` → 正面 / 负面回复 |
| §6 路由函数 | `route_by_sentiment` 返回**节点名** |
| §7 建图 | `add_conditional_edges`；路径列表 / 映射；与 `Command` |
| §8 Invoke | 正负两条推文试跑 |
| 文末实践代码 | 最小可跑示例 |

---

## 1. 定位：从图「一条路」到「按条件分叉」

### 1.1 官方地图里本课在哪

据 [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)：

| 说法 | 含义 | 本课对应 |
| --- | --- | --- |
| **低层编排 runtime** | 管状态、边、持久化、流式、HITL；不替你抽象 Prompt / Agent 架构 | 自己定义 State、节点、条件边 |
| **确定性 + agentic 混用** | 可审计的手写逻辑与 LLM 决策同图 | 路由 = 确定性；分析/回复 = LLM |
| **可不用 LangChain** | 模型/工具常接 LC，但 Graph 本身独立 | 本课用 `ChatOllama`（LC）+ `StateGraph` |
| **更高层另有入口** | 常见 Agent 循环可先看 LangChain Agents；Deep Agents 是其上的 harness | 本系列先啃 Graph API |

LangGraph 后续还会覆盖 persistence、human-in-the-loop、长短期 memory、LangSmith 追踪与部署——本课只落到 **条件边** 这一块。

### 1.2 为何要分叉

[[16_LangGraph]] 里边是固定的：`A → B → C`。真实客服 / 审核流程常要**先分类，再走不同处理**：

```text
START → analyze（LLM 结构化情感）     ← agentic
              │
              ▼
        route_by_sentiment             ← deterministic（读 State，返回节点名）
              ├─ positive → positive_response → END   ← agentic
              └─ negative → negative_response → END   ← agentic
```

| 对比   | LCEL 路由（[[04_Chains]] §6） | 本课 LangGraph                       |
| ---- | ------------------------- | ---------------------------------- |
| 载体   | `RunnableLambda` 返回另一条链   | `StateGraph` + 条件边                 |
| 状态   | 多靠 dict 在链间传递             | 显式 `TypedDict` State，节点只更新部分键      |
| 分支依据 | 分类链输出字符串                  | 路由函数读 State，返回**下一节点名**            |
| 结构化  | 常靠 Prompt「只回一个词」          | `with_structured_output(Pydantic)` |
|      |                           |                                    |

> [!note]
> 条件边的核心不是「再写一个 if 包住整张图」，而是：**分析节点写 State → 路由函数读 State → 图引擎跳到对应节点**（见 [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api#conditional-edges)）。
---

![[828c974b-b4cb-413e-8aaf-18249cfe50ee.png]]
## 2. 场景：Twitter 社媒客服 Agent

### 2.1 学习目标

- 把 LLM 接进 LangGraph 节点（不只做字符串变换）
- 用 **Pydantic `BaseModel` + `with_structured_output()`** 拿结构化结果
- 按情感做 **conditional routing**

### 2.2 可迁移场景

| 场景 | 怎么用同一套路 |
| --- | --- |
| 客服工单 | 按紧急度 / 情感分流话术 |
| 内容审核 | 通过 / 标记；可带 confidence |
| 邮件回复 | 按情感强度调语气 |
| 商品评价 | 分类后匹配强度回复 |
| 社媒运营 | 品牌话术随情感缩放 |

---

## 3. 模型与结构化 Schema

依赖：已 `ollama pull deepseek-r1`（Notebook 用该模型；可换成你本机已有的 chat 模型）。

```python
from typing_extensions import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

BASE_URL = "http://localhost:11434"
MODEL_NAME = "deepseek-r1"

llm = ChatOllama(model=MODEL_NAME, base_url=BASE_URL)
```

### 3.1 `SentimentAnalysis`：给 LLM「填表」

```python
class SentimentAnalysis(BaseModel):
    sentiment: Literal["positive", "negative"] = Field(
        description="The sentiment classification either positive or negative"
    )
    confidence: float = Field(ge=0, le=1.0, description="Confidence score from 0.0 to 1.0")
    reason: str = Field(description="Brief explanation")
```

| 字段 | 作用 |
| --- | --- |
| `sentiment` | 只用 `positive` / `negative`，方便路由 if |
| `confidence` | `0.0`–`1.0`；回复节点可按置信度调语气 |
| `reason` | 简短解释（本课建图未写入 State，可自行扩展） |

对照：[[05_Output Parsing]] 的 `llm.with_structured_output(schema)`。

---

## 4. State：图里共享什么

```python
class SentimentState(TypedDict):
    original_tweet: str
    sentiment: str
    confidence: float
    response_tweet: str
```

| 字段 | 谁写 | 谁读 |
| --- | --- | --- |
| `original_tweet` | `invoke` 初始输入 | 分析节点 + 两个回复节点 |
| `sentiment` / `confidence` | `analyze` | 路由函数；回复 Prompt 也用 confidence |
| `response_tweet` | 正面 / 负面回复节点 | 最终 `invoke` 结果 |

节点仍可**只返回部分键**；图按 schema 合并更新（同 [[16_LangGraph]]）。

---

## 5. 节点

### 5.1 `analyze_sentiment`：结构化分类

```python
def analyze_sentiment(state: SentimentState):
    tweet = state["original_tweet"]
    structured_llm = llm.with_structured_output(SentimentAnalysis)

    messages = [
        SystemMessage(
            "Analyze sentiment and provide the structured output. "
            "Use 0 to 1.0 scale for confidence. lower is negative and higher is positive"
        ),
        HumanMessage(tweet),
    ]

    analysis = structured_llm.invoke(messages)
    return {
        "sentiment": analysis.sentiment,
        "confidence": analysis.confidence,
    }
```

要点：

- 节点入参是整份 State，出参只更新分支需要的字段
- `reason` 算出来了但本课没写回 State（要落盘 / 调试可加 `"reason": analysis.reason`）
- 可单独 `analyze_sentiment({"original_tweet": "Just launched my new product!"})` 测节点

### 5.2 正面 / 负面回复节点

两条对称：读 `original_tweet` + `confidence`，写 `response_tweet`（限制约 280 字，贴近 Tweet）。

| 节点 | 语气 | confidence 怎么用（课例 Prompt） |
| --- | --- | --- |
| `positive_response` | 热情 / 友好 | 高置信 → 更热情；否则友好 |
| `negative_response` | 共情 / 理解 | 置信很低 → 更共情；否则理解 |

```python
def generate_positive_response(state: SentimentState):
    messages = [
        SystemMessage(
            f"""Generate a warm response to this positive tweet under 280 chars.
Confidence: {state['confidence']}. High confidence means be enthusiastic otherwise be friendly."""
        ),
        HumanMessage(state["original_tweet"]),
    ]
    response = llm.invoke(messages)
    return {"response_tweet": response.content.strip()}


def generate_negative_response(state: SentimentState):
    messages = [
        SystemMessage(
            f"""Generate an empathetic response to this negative tweet under 280 chars.
If Confidence {state['confidence']} is very low then be empathetic otherwise be understanding."""
        ),
        HumanMessage(state["original_tweet"]),
    ]
    response = llm.invoke(messages)
    return {"response_tweet": response.content.strip()}
```

> [!note]
> Notebook 函数名是 `generate_postive_response`（拼写少了 i）。下面实践代码用正确拼写；跟跑 Notebook 时改成原名即可。

---

## 6. 路由函数：返回「下一个节点名」

```python
def route_by_sentiment(state: SentimentState):
    if state["sentiment"] == "positive":
        return "positive_response"
    return "negative_response"
```

官方语义（[Conditional edges](https://docs.langchain.com/oss/python/langgraph/graph-api#conditional-edges)）：

| 要点 | 说明 |
| --- | --- |
| 入参 | 与节点一样，吃**当前整份 State** |
| 默认返回值 | 直接当作**下一节点名**（也可返回节点名列表 → 下一 superstep 并行跑） |
| 本课返回值 | 字符串 = `add_node` 注册名，不是函数对象 |
| 读什么 | 只读上游已写入的字段（这里是 `sentiment`） |
| 默认分支 | 课例非 `positive` 一律走负面（未单独处理异常标签） |

这就是 overview 说的 **deterministic step**：分支逻辑可审计、可单测，不交给模型「自己决定下一步叫什么」。

---

## 7. 建图：`add_conditional_edges`

```python
def create_router_graph():
    builder = StateGraph(SentimentState)

    builder.add_node("analyze", analyze_sentiment)
    builder.add_node("positive_response", generate_positive_response)
    builder.add_node("negative_response", generate_negative_response)

    builder.add_edge(START, "analyze")
    builder.add_conditional_edges(
        "analyze",
        route_by_sentiment,
        ["positive_response", "negative_response"],
    )
    builder.add_edge("positive_response", END)
    builder.add_edge("negative_response", END)

    return builder.compile()
```

| API | 作用 |
| --- | --- |
| `add_edge(START, "analyze")` | 固定入口（normal edge） |
| `add_conditional_edges(源, 路由函数, …)` | 源节点跑完后调用路由函数决定下一跳 |
| `add_edge(..., END)` | 两条支路汇入结束 |
| `compile()` | → 可 `invoke` 的 Runnable |

### 7.1 第三参：路径列表 vs 映射 dict

| 写法 | 含义 |
| --- | --- |
| 列表 `["positive_response", "negative_response"]`（课例） | 声明合法去向；函数返回值须是其中某个**节点名** |
| 映射 `{True: "node_b", False: "node_c"}` | 函数可返回 `True`/`False` 等键，由 dict 翻成节点名 |
| 省略第三参 | 函数返回值直接当节点名（或节点名列表） |

也可从 `START` 上挂条件边，做**条件入口**（本课用固定 `START → analyze`）。

### 7.2 与 `Command`、普通边的边界（官方提示）

| 需求 | 用什么 |
| --- | --- |
| 只路由、不更新 State | **条件边**（本课） |
| 同一函数里既 `update` State 又 `goto` | [`Command`](https://docs.langchain.com/oss/python/langgraph/graph-api#command) |
| 同一节点 | **不要**同时挂普通边 + 条件边 / `Command` 动态跳转，否则可能两条路径都执行 |

本课拆成「分析节点写字段 + 独立路由函数」，正是条件边的典型用法。
---

## 8. Invoke：正负各跑一遍

```python
graph = create_router_graph()

# 正面
graph.invoke({
    "original_tweet": (
        "Just launched my new product! the response from everyone has been amazing so far."
    )
})

# 负面
graph.invoke({
    "original_tweet": "Really disappointed with the service I received today."
})
```

预期形态（字段值随模型变化）：

```text
original_tweet: …
sentiment: positive | negative
confidence: 0.x
response_tweet: （短回复，约 ≤280 字）
```

调试时看节点里的 `print`：分析阶段打印推文与 `SentimentAnalysis`；回复阶段打印进入该节点时的完整 State。

---

## 实践代码（最小可跑）

依赖：`langgraph`、`langchain-ollama`、`langchain-core`、`pydantic`、`typing_extensions`（环境见 [[杂项]]）。需本机 Ollama 已拉模型。

```python
from typing_extensions import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

llm = ChatOllama(model="deepseek-r1", base_url="http://localhost:11434")


class SentimentAnalysis(BaseModel):
    sentiment: Literal["positive", "negative"] = Field(
        description="positive or negative"
    )
    confidence: float = Field(ge=0, le=1.0, description="0.0 to 1.0")
    reason: str = Field(description="Brief explanation")


class SentimentState(TypedDict):
    original_tweet: str
    sentiment: str
    confidence: float
    response_tweet: str


def analyze_sentiment(state: SentimentState):
    structured_llm = llm.with_structured_output(SentimentAnalysis)
    analysis = structured_llm.invoke(
        [
            SystemMessage(
                "Analyze sentiment. confidence 0–1; lower leans negative, higher positive."
            ),
            HumanMessage(state["original_tweet"]),
        ]
    )
    return {"sentiment": analysis.sentiment, "confidence": analysis.confidence}


def generate_positive_response(state: SentimentState):
    response = llm.invoke(
        [
            SystemMessage(
                f"Warm reply under 280 chars. Confidence={state['confidence']}: "
                "high → enthusiastic, else friendly."
            ),
            HumanMessage(state["original_tweet"]),
        ]
    )
    return {"response_tweet": response.content.strip()}


def generate_negative_response(state: SentimentState):
    response = llm.invoke(
        [
            SystemMessage(
                f"Empathetic reply under 280 chars. Confidence={state['confidence']}: "
                "very low → more empathetic, else understanding."
            ),
            HumanMessage(state["original_tweet"]),
        ]
    )
    return {"response_tweet": response.content.strip()}


def route_by_sentiment(state: SentimentState):
    if state["sentiment"] == "positive":
        return "positive_response"
    return "negative_response"


def create_router_graph():
    builder = StateGraph(SentimentState)
    builder.add_node("analyze", analyze_sentiment)
    builder.add_node("positive_response", generate_positive_response)
    builder.add_node("negative_response", generate_negative_response)
    builder.add_edge(START, "analyze")
    builder.add_conditional_edges(
        "analyze",
        route_by_sentiment,
        ["positive_response", "negative_response"],
    )
    builder.add_edge("positive_response", END)
    builder.add_edge("negative_response", END)
    return builder.compile()


graph = create_router_graph()
print(graph.invoke({"original_tweet": "Just launched my new product! Amazing response so far."}))
print(graph.invoke({"original_tweet": "Really disappointed with the service I received today."}))
```

---

## 速查

| API / 概念 | 作用 |
| --- | --- |
| [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) | 低层编排；确定性步骤 + LLM 步骤同图 |
| `llm.with_structured_output(Model)` | 节点内拿到 Pydantic 对象，而不是裸字符串 |
| `Literal[...]` + `Field` | 收紧标签与数值范围，方便路由 |
| `add_conditional_edges(src, fn, …)` | 条件边；`fn(state)` 返回节点名 / 键 / 列表 |
| 路由函数 | 确定性决策；一般不写回复内容 |
| 回复节点 | 读 State，写 `response_tweet`；可用 `confidence` 调语气 |
| `Command` | 同一节点内「更新 State + 跳转」时用；本课未用 |

---

## 相关笔记

- [[16_LangGraph]] — State / Node / 固定边；本课补条件边
- [[04_Chains]] — LCEL 路由链（情感 → 正负回复）同一业务、不同编排
- [[05_Output Parsing]] — `with_structured_output` 细节
- [[杂项]] — Conda / 依赖环境

## 待处理

- [ ] 把 Notebook 内嵌架构图导出进库（若需要图示）
- [ ] 可选：把 `reason` 写入 State，或加 `neutral` / 置信度阈值分支
- [ ] 后续课可接：persistence / interrupt（HITL）/ LangSmith tracing（overview 列出的核心能力）
