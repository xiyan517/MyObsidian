---
title: Chains
aliases:
  - LCEL
  - LangChain Expression Language
  - Runnable
  - 链式调用
created: 2026-08-01
updated: 2026-08-01
series: 本地 RAG
part: 4
source: Chains.ipynb（可删）· 字幕 043–054（可删）
tags:
  - type/literature-note
  - topic/langchain
  - topic/lcel
  - topic/ollama
  - topic/local-rag
  - status/draft
---

# Chains（LCEL 链式组合）

> [!summary]
> **本地 RAG · 第 4 部分**。用 **LCEL**（`|` / `.pipe()`）把 Runnable 串成链：顺序链 → `StrOutputParser` → 链套链 → **并行** → **路由** → `RunnableLambda` / `RunnablePassthrough` / **`@chain`**。一次 `chain.invoke(params)` 跑完全流程。

默认：`ChatOllama(base_url="http://localhost:11434", model="qwen3")`。

## 本章目录

| 章节 | 学什么 |
| --- | --- |
| §1 LCEL 是什么 | Runnable、`|`、链类型一览 |
| §2 第一条顺序链 | `template \| llm`；对比分步 invoke |
| §3 StrOutputParser | 从 AIMessage 只取字符串 |
| §4 链套链 | `{"response": chain} \| …` 做生成后再分析 |
| §5 并行链 | `RunnableParallel`；fact + poem |
| §6 路由链 | 评论情感 → 正面 / 负面回复 |
| §7 Lambda / Passthrough | 自定义函数 + 保留原文 |
| §8 `@chain` | 装饰器把函数变成 Runnable |
| 文末实践代码 | 可复跑主路径 |

---

## 1. LCEL 是什么

**LangChain Expression Language**：任意两个 Runnable 可串成序列——上一步 `.invoke()` 的输出，自动成为下一步的输入。写法：

- 管道符：`a | b | c`
- 或显式：`a.pipe(b).pipe(c)`（等价）

**Runnable** = 可被 invoke 的任务单元。常见成员：

| 组件 | 也是 Runnable？ |
| --- | --- |
| `ChatPromptTemplate` / 各类 Message Prompt Template | 是 |
| `ChatOllama`（→ BaseChatModel → Runnable） | 是 |
| 由它们组成的 **Chain 本身** | 也是 |
| `StrOutputParser`、`RunnableLambda` 等 | 是 |

**以前**：`template.invoke(...)` → 再 `llm.invoke(question)`，多步手写。  
**现在**：`chain = template | llm`，变量一次性交给 `chain.invoke(...)`。

课程中的链类型：

| 类型 | 作用 |
| --- | --- |
| Sequential | 按顺序串 |
| Parallel | 互不依赖时并行 |
| Router | 按上一步结果选下游链 |
| Custom | `RunnableLambda` / `Passthrough` / `@chain` |

若配置了 LangSmith，Runnable 执行会进追踪，便于看每一步。

---

## 2. 第一条顺序链

### 2.1 旧写法（分步）

```python
from langchain_ollama import ChatOllama
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)

llm = ChatOllama(base_url="http://localhost:11434", model="qwen3")

system = SystemMessagePromptTemplate.from_template(
    "You are {school} teacher. You answer in short sentences."
)
question = HumanMessagePromptTemplate.from_template(
    "tell me about the {topics} in {points} points"
)
template = ChatPromptTemplate([system, question])

prompt_value = template.invoke(
    {"school": "primary", "topics": "solar system", "points": 5}
)
response = llm.invoke(prompt_value)
print(response.content)
```

### 2.2 新写法（LCEL）

```python
chain = template | llm
response = chain.invoke(
    {"school": "primary", "topics": "solar system", "points": 5}
)
print(response.content)
```

`school` / `topics` / `points` **直接传给 chain**；chain 的 `input_variables` 会合并模板里的变量。换 `school: "phd"` 即可换语气，不必重写管道。

无 parser 时返回仍是 **`AIMessage`**，取文本用 `.content`。

---

## 3. 加上 `StrOutputParser`

LLM 返回完整 `AIMessage`（`content` + `response_metadata` 等）。后面还要接别的 Runnable 时，整包对象会碍事。

```python
from langchain_core.output_parsers import StrOutputParser

chain = template | llm | StrOutputParser()
response = chain.invoke(
    {"school": "primary", "topics": "solar system", "points": 5}
)
print(response)  # 已是 str，不用 .content
```

| 步骤 | 输出类型 |
| --- | --- |
| `template \| llm` | `AIMessage` |
| `… \| StrOutputParser()` | `str`（只留 content） |

复杂序列里统一成字符串，后面才好拼。

---

## 4. 链套链（多个 Runnable 串联）

场景：

1. **chain**：按学校级别生成 solar system 知识点（已有 `template | llm | StrOutputParser()`）
2. **fact_check_chain**：分析这段文字好不好懂，**只用一句话**回答

单独测分析链：

```python
analysis_prompt = ChatPromptTemplate.from_template(
    """analyze the following text: {response}
You need tell me that how difficult it is to understand.
Answer in one sentence only.
"""
)
fact_check_chain = analysis_prompt | llm | StrOutputParser()
print(fact_check_chain.invoke({"response": response}))
```

**组合**：用字典把上一条链的输出映射到下一模板的 `{response}`：

```python
composed_chain = {"response": chain} | analysis_prompt | llm | StrOutputParser()

print(
    composed_chain.invoke(
        {"school": "phd", "topics": "solar system", "points": 5}
    )
)
```

```text
params → chain（生成）→ 键名 response
       → analysis_prompt | llm | StrOutputParser（评估）
```

最终 `invoke` 返回的是**分析句**；生成原文可在 LangSmith 嵌套步骤里看。「生成 + 再评估」是后续 RAG 里常见模式。

> [!note]
> 依赖上一步输出的链**不能**和上游并行，只能接在后面（顺序）。

---

## 5. 并行链

### 5.1 何时可并行

两条链**互不依赖**才能并行。  
反例：fact_check 依赖 fact 输出 → 必须顺序。  
正例：知识点链 + 写诗链，共享部分入参、互不等待。

### 5.2 先分别建两条链

```python
system = SystemMessagePromptTemplate.from_template(
    "You are {school} teacher. You answer in short sentences."
)

fact_template = ChatPromptTemplate(
    [
        system,
        HumanMessagePromptTemplate.from_template(
            "tell me about the {topics} in {points} points"
        ),
    ]
)
fact_chain = fact_template | llm | StrOutputParser()

poem_template = ChatPromptTemplate(
    [
        system,
        HumanMessagePromptTemplate.from_template(
            "write a poem on {topics} in {sentences} lines"
        ),
    ]
)
poem_chain = poem_template | llm | StrOutputParser()
```

### 5.3 `RunnableParallel`

```python
from langchain_core.runnables import RunnableParallel

parallel = RunnableParallel(fact=fact_chain, poem=poem_chain)

output = parallel.invoke(
    {
        "school": "primary",
        "topics": "solar system",
        "points": 2,
        "sentences": 2,
    }
)
print(output["fact"])
print(output["poem"])
```

| 点 | 说明 |
| --- | --- |
| 返回值 | **dict**，键是你起的名字（`fact` / `poem`） |
| 入参 | 一次传齐所有变量（含 `points` 与 `sentences`） |
| 延迟直觉 | 顺序 ≈ t1+t2；并行 ≈ max(t1,t2)（要有足够算力） |

同模块里还有 `RunnableLambda`、`RunnablePassthrough`、以及 `RunnableSequence` / `RunnableBranch` 等（本课主用前几个）。

---

## 6. 路由链（Router）

### 6.1 在干什么

```text
用户输入
  → 通用链（分类）
  → Router 按标签选链
  → 专用链 A 或 B → 最终回答
```

类比：同一入口，内部按类型走不同模型/话术。本课用**客户评论情感**演示。

### 6.2 三条独立链

**① 分类**（只回一个词 `Positive` / `Negative`）

```python
classify_prompt = """Given the user review below, classify it as either being about `Positive` or `Negative`.
Do not respond with more than one word.

Review: {review}
Classification:"""

classify_chain = (
    ChatPromptTemplate.from_template(classify_prompt) | llm | StrOutputParser()
)
```

**② 正面回复**：鼓励分享到社交媒体  

**③ 负面回复**：先道歉，引导发邮件（课例：`udemy@kgptalkie.com`）

```python
positive_chain = (
    ChatPromptTemplate.from_template(
        """
You are expert in writing reply for positive reviews.
You need to encourage the user to share their experience on social media.
Review: {review}
Answer:"""
    )
    | llm
    | StrOutputParser()
)

negative_chain = (
    ChatPromptTemplate.from_template(
        """
You are expert in writing reply for negative reviews.
You need first to apologize for the inconvenience caused to the user.
You need to encourage the user to share their concern on following Email:'udemy@kgptalkie.com'.
Review: {review}
Answer:"""
    )
    | llm
    | StrOutputParser()
)
```

### 6.3 路由函数 + `RunnableLambda`

```python
from langchain_core.runnables import RunnableLambda

def rout(info):
    if "positive" in info["sentiment"].lower():
        return positive_chain
    return negative_chain

full_chain = {
    "sentiment": classify_chain,
    "review": lambda x: x["review"],  # 透传原文给下游
} | RunnableLambda(rout)

print(
    full_chain.invoke(
        {
            "review": "I am not happy with the service. It is not good."
        }
    )
)
```

| 键 / 组件 | 作用 |
| --- | --- |
| `sentiment` | 跑分类链 |
| `review` | 保留原始评论，供正/负面链用 `{review}` |
| `RunnableLambda(rout)` | 普通函数变成 Runnable；**返回要执行的那条链** |
| `.lower()` | 兼容 `Positive` / `POSITIVE` / `positive` |

一次 `invoke({"review": ...})`：自动分类 → 选链 → 生成回复。

---

## 7. `RunnableLambda` 与 `RunnablePassthrough`

| 工具 | 作用 |
| --- | --- |
| `RunnableLambda(fn)` | 把任意 Python 函数嵌进 `|` 管道 |
| `RunnablePassthrough()` | 把上游输入**原样**传到下游（不改、不丢） |

内置 prompt / LLM / parser 不够用时，用它们塞自定义逻辑（格式化、统计、选链等）。

### 7.1 生成后再统计字数 / 词数

问题：若只接 `RunnableLambda(char_counts)`，会**丢掉** LLM 原文。  
做法：字典并行——统计 + **Passthrough 保留 output**。

```python
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

def char_counts(text):
    return len(text)

def word_counts(text):
    return len(text.split())

prompt = ChatPromptTemplate.from_template(
    "Explain these inputs in 5 sentences: {input1} and {input2}"
)

chain = (
    prompt
    | llm
    | StrOutputParser()
    | {
        "char_counts": RunnableLambda(char_counts),
        "word_counts": RunnableLambda(word_counts),
        "output": RunnablePassthrough(),
    }
)

print(
    chain.invoke({"input1": "Earth is planet", "input2": "Sun is star"})
)
# → {'char_counts': …, 'word_counts': …, 'output': '…'}
```

比让 LLM「自己数词」更准。

---

## 8. `@chain` 装饰器

把整段函数一键变成 LCEL Runnable（复杂编排时比到处包 `RunnableLambda` 更清晰）。

```python
from langchain_core.runnables import chain  # 装饰器

@chain
def custom_chain(params):
    return {
        "fact": fact_chain.invoke(params),
        "poem": poem_chain.invoke(params),
    }

params = {
    "school": "primary",
    "topics": "solar system",
    "points": 2,
    "sentences": 2,
}
output = custom_chain.invoke(params)
print(output["fact"])
print(output["poem"])
```

> [!warning]
> 导入 `@chain` 后，**不要**再写 `chain = template | llm` 覆盖同名；顺序链请用 `fact_chain` / `poem_chain` 等名字。

`@chain` ≈ 用装饰器注册函数为 Runnable；函数体内可任意调用已有链。

---

## LCEL 模式速查

| 模式 | 写法 | 输出 |
| --- | --- | --- |
| 顺序 | `a \| b \| c` | 最后一步结果 |
| 键映射接下一链 | `{"key": chain1} \| prompt \| …` | 下游按 key 取上游输出 |
| 并行 | `RunnableParallel(x=c1, y=c2)` | `{"x": …, "y": …}` |
| 路由 | `{…} \| RunnableLambda(route_fn)` | route_fn 返回的那条链的执行结果 |
| 自定义函数 | `RunnableLambda(fn)` | fn 返回值 |
| 透传 | `RunnablePassthrough()` | 上游值不变 |
| 装饰器 | `@chain def foo(x): …` | 整个函数可 `.invoke` |

```text
顺序 → 并行（RunnableParallel）
    → 路由（RunnableLambda 返回链）
    → 自定义（Lambda + Passthrough / @chain）
```

---

## 文末实践代码

```python
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnableParallel,
    RunnableLambda,
    RunnablePassthrough,
    chain,
)

load_dotenv("./../.env")

llm = ChatOllama(base_url="http://localhost:11434", model="qwen3")

# --- 1) 顺序链 + StrOutputParser ---
system = SystemMessagePromptTemplate.from_template(
    "You are {school} teacher. You answer in short sentences."
)
human = HumanMessagePromptTemplate.from_template(
    "tell me about the {topics} in {points} points"
)
template = ChatPromptTemplate([system, human])
gen_chain = template | llm | StrOutputParser()
print(gen_chain.invoke({"school": "primary", "topics": "solar system", "points": 3}))

# --- 2) 链套链：生成后再分析 ---
analysis_prompt = ChatPromptTemplate.from_template(
    """analyze the following text: {response}
Answer in one sentence how difficult it is to understand."""
)
composed = {"response": gen_chain} | analysis_prompt | llm | StrOutputParser()
print(composed.invoke({"school": "phd", "topics": "solar system", "points": 3}))

# --- 3) 并行 ---
poem_template = ChatPromptTemplate(
    [
        system,
        HumanMessagePromptTemplate.from_template(
            "write a poem on {topics} in {sentences} lines"
        ),
    ]
)
fact_chain = gen_chain
poem_chain = poem_template | llm | StrOutputParser()
parallel = RunnableParallel(fact=fact_chain, poem=poem_chain)
print(
    parallel.invoke(
        {
            "school": "primary",
            "topics": "solar system",
            "points": 2,
            "sentences": 2,
        }
    )
)

# --- 4) 路由（评论）---
classify_chain = (
    ChatPromptTemplate.from_template(
        """Given the user review below, classify it as either being about `Positive` or `Negative`.
Do not respond with more than one word.
Review: {review}
Classification:"""
    )
    | llm
    | StrOutputParser()
)
positive_chain = (
    ChatPromptTemplate.from_template(
        """You are expert in writing reply for positive reviews.
Encourage sharing on social media.
Review: {review}
Answer:"""
    )
    | llm
    | StrOutputParser()
)
negative_chain = (
    ChatPromptTemplate.from_template(
        """You are expert in writing reply for negative reviews.
First apologize, then ask them to email udemy@kgptalkie.com.
Review: {review}
Answer:"""
    )
    | llm
    | StrOutputParser()
)

def rout(info):
    if "positive" in info["sentiment"].lower():
        return positive_chain
    return negative_chain

full_chain = {
    "sentiment": classify_chain,
    "review": lambda x: x["review"],
} | RunnableLambda(rout)
print(full_chain.invoke({"review": "I am not happy with the service."}))

# --- 5) Lambda + Passthrough ---
def char_counts(text):
    return len(text)

def word_counts(text):
    return len(text.split())

stats_chain = (
    ChatPromptTemplate.from_template(
        "Explain these inputs in 5 sentences: {input1} and {input2}"
    )
    | llm
    | StrOutputParser()
    | {
        "char_counts": RunnableLambda(char_counts),
        "word_counts": RunnableLambda(word_counts),
        "output": RunnablePassthrough(),
    }
)
print(stats_chain.invoke({"input1": "Earth is planet", "input2": "Sun is star"}))

# --- 6) @chain（注意：不要用变量名 chain 覆盖装饰器）---
@chain
def custom_parallel(params):
    return {
        "fact": fact_chain.invoke(params),
        "poem": poem_chain.invoke(params),
    }

print(
    custom_parallel.invoke(
        {
            "school": "primary",
            "topics": "solar system",
            "points": 2,
            "sentences": 2,
        }
    )
)
```
