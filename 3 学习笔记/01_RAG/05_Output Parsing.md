---
title: Output Parsing
aliases:
  - 输出解析
  - PydanticOutputParser
  - JsonOutputParser
  - with_structured_output
created: 2026-08-01
updated: 2026-08-01
series: 本地 RAG
part: 5
source: Output Parsing.ipynb（可删）· 字幕 055–061（可删）
tags:
  - type/literature-note
  - topic/langchain
  - topic/output-parser
  - topic/pydantic
  - topic/ollama
  - topic/local-rag
  - status/draft
---

# Output Parsing（结构化输出）

> [!summary]
> **本地 RAG · 第 5 部分**。LLM 默认吐文本 / `AIMessage`；用 Output Parser 变成 **str / Pydantic 对象 / dict / 逗号分隔列表**。两条能力：**`get_format_instructions()`** 写进 Prompt，**parse / 链尾 `| parser`** 解析结果。另有捷径：`llm.with_structured_output(schema)`。

默认：`ChatOllama(base_url="http://localhost:11434", model="qwen3")`。结构化输出不稳定时可换更大模型（课里曾用 `llama3.2:3b` 量级）。

## 本章目录

| 章节 | 学什么 |
| --- | --- |
| §1 为什么要解析 | 两大方法；本课 parser 一览 |
| §2 Pydantic Parser | `BaseModel` + `Field` + `PydanticOutputParser` |
| §3 注入指令并解析 | `partial_variables` → `prompt \| llm \| parser` |
| §4 `with_structured_output` | 模型直接绑 schema |
| §5 JsonOutputParser | 同 schema，结果是 `dict` |
| §6 逗号分隔列表 | `CommaSeparatedListOutputParser` |
| 文末实践代码 | 可复跑主路径 |

---

## 1. 为什么要解析

语言模型输出是文本。业务常要 **结构化字段**（笑话的 setup/punchline、SEO 关键词列表等）。

Output Parser 必须实现（概念上）两类能力：

| 方法 | 作用 |
| --- | --- |
| **Get format instructions** | 返回一段说明，告诉模型「按什么格式写」 |
| **Parse** | 把模型字符串解析成目标结构 |

```text
LLM → AIMessage / 文本
  → Output Parser
  → str / JSON / Pydantic / list …
```

已在 Chains 里用过的 **`StrOutputParser`**：链尾 `| StrOutputParser()` 后直接得 `str`，不用再 `.content`。

本课覆盖：

| Parser / 方式 | 典型结果 |
| --- | --- |
| `StrOutputParser` | `str`（复习） |
| `PydanticOutputParser` | **Pydantic 实例** |
| `llm.with_structured_output(schema)` | Pydantic / 结构化对象 |
| `JsonOutputParser` | **`dict`** |
| `CommaSeparatedListOutputParser` | **`list[str]`** |
| Datetime Output Parser | Notebook 注明：Langchain v1 **暂不可用** |

> [!note]
> LangSmith 会上传 trace；私有数据可改用 Langfuse / Opik 等自托管方案。

---

## 2. Pydantic Parser：用 schema 定义形状

### 2.1 Pydantic 在这里干什么

用 **`BaseModel` + `Field(description=...)`** 声明字段名、类型与说明。`description` 会进 format instructions，帮模型填对字段。

```python
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser

class Joke(BaseModel):
    """Joke to tell user"""

    setup: str = Field(description="The setup of the joke")
    punchline: str = Field(description="The punchline of the joke")
    rating: Optional[int] = Field(
        description="The rating of the joke is from 1 to 10",
        default=None,
    )

parser = PydanticOutputParser(pydantic_object=Joke)
```

### 2.2 看自动生成的指令

```python
instruction = parser.get_format_instructions()
print(instruction)
```

内容大意：要求输出符合 JSON schema 的实例，并附上 `Joke` 的 properties（`setup` / `punchline` / `rating`）。你只写了少量 Field，parser 在后台拼好整段说明。

---

## 3. 注入指令并解析

### 3.1 Prompt：`input_variables` vs `partial_variables`

本课用 **`PromptTemplate`**（单段文本），占位符与 notebook 一致：`{format_instruction}`、`{query}`。

| 变量类型 | 例子 | 何时填 |
| --- | --- | --- |
| `input_variables` | `query` | 每次 `invoke` |
| `partial_variables` | `format_instruction` | 建模板时预填，固定不变 |

```python
from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate(
    template="""
    Answer the user query with a joke. Here is your formatting instruction.
    {format_instruction}

    Query: {query}
    Answer:""",
    input_variables=["query"],
    partial_variables={
        "format_instruction": parser.get_format_instructions()
    },
)
```

### 3.2 两阶段对比

```python
# 只有 LLM：content 里已是 JSON 形态文本，仍是 AIMessage
chain = prompt | llm
raw = chain.invoke({"query": "Tell me a joke about the cat"})
print(raw.content)

# 接上 parser：得到 Joke 对象
chain = prompt | llm | parser
joke = chain.invoke({"query": "Tell me a joke about the dogs"})
print(joke)            # setup='...' punchline='...' rating=8
print(joke.setup)
print(joke.punchline)
print(joke.rating)
```

```text
query + format_instruction
  → PromptTemplate
  → ChatOllama
  → PydanticOutputParser
  → Joke 实例
```

> [!tip]
> 过小模型（如 ~1B）工具/结构化能力弱，容易解析失败；课里结构化演示偏向 **≥3B**。

---

## 4. `.with_structured_output()`：少写几步

不单独建 Parser、不手动 `partial_variables`，把 schema 绑到模型上：

```python
structured_llm = llm.with_structured_output(Joke)
output = structured_llm.invoke("Tell me a joke about the cat")
print(output)  # Joke 实例；无需 .content，也无需链尾 parser
```

文档口径：schema 可以是 **Pydantic 类 / TypedDict / JSON Schema**。

| 方式 | 优点 | 注意 |
| --- | --- | --- |
| `with_structured_output()` | 代码最短 | 绑在 LLM 上；和别的 Runnable 组合时要想好边界 |
| `PydanticOutputParser` + 链 | Parser 独立，管道灵活 | 步骤更多 |

未绑 schema 时 `llm.invoke("Tell me a joke…")` 常是自由散文；绑了之后强制字段。

---

## 5. `JsonOutputParser`：同 schema，结果是 dict

流程几乎同 Pydantic Parser，差别在**返回类型**：

| Parser | 返回 |
| --- | --- |
| `PydanticOutputParser` | `Joke` 实例 → `output.setup` |
| `JsonOutputParser` | `dict` → `output["setup"]` |

```python
from langchain_core.output_parsers import JsonOutputParser

parser = JsonOutputParser(pydantic_object=Joke)
print(parser.get_format_instructions())  # 与 Pydantic 版类似的 schema 说明

prompt = PromptTemplate(
    template="""
    Answer the user query with a joke. Here is your formatting instruction.
    {format_instruction}

    Query: {query}
    Answer:""",
    input_variables=["query"],
    partial_variables={
        "format_instruction": parser.get_format_instructions()
    },
)

chain = prompt | llm | parser
output = chain.invoke({"query": "Tell me a joke about the cat"})
print(output)           # {'setup': '...', 'punchline': '...', 'rating': 8}
print(type(output))     # dict
print(output["setup"])
```

同一套 `Joke` 类可复用于：`PydanticOutputParser` / `JsonOutputParser` / `with_structured_output`。

---

## 6. CSV 列表：`CommaSeparatedListOutputParser`

要 **逗号分隔列表**（如 SEO 关键词），不需要 Pydantic 类。

```python
from langchain_core.output_parsers import CommaSeparatedListOutputParser

parser = CommaSeparatedListOutputParser()
print(parser.get_format_instructions())
# 大意：Your response should be a list of comma separated values, eg: `foo, bar, baz`

prompt = PromptTemplate(
    template="""
    Answer the user query with a list of values. Here is your formatting instruction.
    {format_instruction}

    Query: {query}
    Answer:""",
    input_variables=["query"],
    partial_variables={
        "format_instruction": parser.get_format_instructions()
    },
)

chain = prompt | llm | parser
output = chain.invoke(
    {
        "query": "generate my website seo keywords. I have content about the NLP and LLM."
    }
)
print(output)  # ['natural language processing', 'llm', ...] 一类 list[str]
```

不加 format instruction 时，模型常吐 Markdown / 编号列表；加上后更容易变成标准逗号列表并被解析成 Python `list`。

---

## 四种方式对照（同一 Joke）

```python
# ① Pydantic 对象
PydanticOutputParser(pydantic_object=Joke)

# ② dict
JsonOutputParser(pydantic_object=Joke)

# ③ 绑在 LLM 上 → Pydantic 对象
llm.with_structured_output(Joke)

# ④ 逗号列表（无 Joke schema）
CommaSeparatedListOutputParser()
```

| 需求 | 优先 |
| --- | --- |
| 要类型校验 / 属性访问 | `PydanticOutputParser` 或 `with_structured_output` |
| 只要 dict 给下游 JSON | `JsonOutputParser` |
| 关键词 / 标签列表 | `CommaSeparatedListOutputParser` |
| 只要纯文本 | `StrOutputParser` |

---

## 文末实践代码

```python
from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import (
    PydanticOutputParser,
    JsonOutputParser,
    CommaSeparatedListOutputParser,
)

load_dotenv("./../.env")

llm = ChatOllama(base_url="http://localhost:11434", model="qwen3")


class Joke(BaseModel):
    """Joke to tell user"""

    setup: str = Field(description="The setup of the joke")
    punchline: str = Field(description="The punchline of the joke")
    rating: Optional[int] = Field(
        description="The rating of the joke is from 1 to 10",
        default=None,
    )


# --- 1) PydanticOutputParser ---
pyd_parser = PydanticOutputParser(pydantic_object=Joke)
pyd_prompt = PromptTemplate(
    template="""
    Answer the user query with a joke. Here is your formatting instruction.
    {format_instruction}

    Query: {query}
    Answer:""",
    input_variables=["query"],
    partial_variables={
        "format_instruction": pyd_parser.get_format_instructions()
    },
)
joke = (pyd_prompt | llm | pyd_parser).invoke(
    {"query": "Tell me a joke about the dogs"}
)
print(joke, joke.setup, joke.punchline, joke.rating)

# --- 2) with_structured_output ---
structured_llm = llm.with_structured_output(Joke)
print(structured_llm.invoke("Tell me a joke about the cat"))

# --- 3) JsonOutputParser → dict ---
json_parser = JsonOutputParser(pydantic_object=Joke)
json_prompt = PromptTemplate(
    template="""
    Answer the user query with a joke. Here is your formatting instruction.
    {format_instruction}

    Query: {query}
    Answer:""",
    input_variables=["query"],
    partial_variables={
        "format_instruction": json_parser.get_format_instructions()
    },
)
print((json_prompt | llm | json_parser).invoke({"query": "Tell me a joke about the cat"}))

# --- 4) CommaSeparatedListOutputParser ---
csv_parser = CommaSeparatedListOutputParser()
csv_prompt = PromptTemplate(
    template="""
    Answer the user query with a list of values. Here is your formatting instruction.
    {format_instruction}

    Query: {query}
    Answer:""",
    input_variables=["query"],
    partial_variables={
        "format_instruction": csv_parser.get_format_instructions()
    },
)
print(
    (csv_prompt | llm | csv_parser).invoke(
        {
            "query": "generate my website seo keywords. I have content about the NLP and LLM."
        }
    )
)
```
