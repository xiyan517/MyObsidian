---
title: Chat with Your Own Documents
aliases:
  - RAG 问答
  - Retrieval Augmented Generation
  - as_retriever
created: 2026-07-27
updated: 2026-08-01
series: 本地 RAG
part: 10
source: RAG - Chat with Your Own Documents.ipynb（可删）· 字幕 116–121（可删）
tags:
  - type/literature-note
  - topic/rag
  - topic/faiss
  - topic/langchain
  - topic/ollama
  - topic/local-rag
  - status/draft
---

# Chat with Your Own Documents（检索增强生成）

> [!summary]
> **本地 RAG · 第 10 部分**。接上节已落盘的 FAISS：`load_local` → `as_retriever`（similarity / MMR / threshold）→ RAG Prompt + LCEL 链 → `ChatOllama` 基于检索 context 作答。Embedding 必须与入库时一致（`nomic-embed-text`）。

数据：<https://github.com/laxmimerit/rag-dataset>  
向量库路径课例：`../09. Vector Stores and Retrievals/health_supplements`

## 本章目录

| 章节 | 学什么 |
| --- | --- |
| §1 检索生成流 | 问题 → 检索 → LLM |
| §2 加载向量库 | `load_local`、embedding 一致 |
| §3 Retriever | `as_retriever`、三种 search_type |
| §4 Prompt 与 LCEL 链 | `format_docs`、`RunnablePassthrough` |
| §5 调参 | Prompt / 检索侧经验 |
| 文末实践代码 | 完整可跑骨架 |

---

## 1. 检索生成流

![[10-rag-cell3-0.png]]

![[10-rag-cell4-1.png]]

```text
Question
  → Embedding（同一 nomic-embed-text）
  → FAISS 相似度检索 → Top-K chunks（context）
  → Prompt(context + question) → ChatOllama → Answer
```

上节完成**入库**；本节完成 **Retrieval + Augmented Generation**。

---

## 2. 加载已保存的向量库

```bash
# 环境（与 §9 相同）
# pip install faiss-cpu langchain-community langchain-ollama …
# ollama pull nomic-embed-text
```

```python
import os
import warnings
from dotenv import load_dotenv

os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
warnings.filterwarnings("ignore")
load_dotenv()

from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434",
)

db_name = r"..\09. Vector Stores and Retrievals\health_supplements"
vector_store = FAISS.load_local(
    db_name,
    embeddings,
    allow_dangerous_deserialization=True,  # 允许反序列化 index.pkl
)
```

| 注意 | 说明 |
| --- | --- |
| Embedding 一致 | 与 `save_local` 时同一模型，否则检索失效 |
| `allow_dangerous_deserialization` | pickle 安全策略；只加载自己建的库 |
| 路径 | Windows 用 raw string `r"..."` 或正斜杠 |
| 目录内容 | `index.faiss` + `index.pkl` |

先验证库能搜：

```python
question = "how to gain muscle mass?"
docs = vector_store.search(query=question, k=5, search_type="similarity")
```

---

## 3. `as_retriever`：给 LCEL 用的检索器

LCEL 链侧需要 **Retriever**（`.invoke(question)`），不是直接拿 `VectorStore` 塞进管道。

```python
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3},
)
retriever.invoke("how to lose weight?")
```

检索参数在 `as_retriever` 时配好，之后每次 `invoke` 复用。

### 三种 `search_type`

| 类型 | 做什么 | 常用 kwargs |
| --- | --- | --- |
| **`similarity`** | 按相似度取 Top-K | `k` |
| **`similarity_score_threshold`** | 相似度 ≥ 阈值，再最多取 K 条 | `k`、`score_threshold`（约 0–1） |
| **`mmr`** | 先取 `fetch_k` 候选，再按 MMR 选 K 条（相关 + 多样） | `k`、`fetch_k`、`lambda_mult` |

```python
# 阈值过滤（太高可能空结果；课例 0.1）
retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 3, "score_threshold": 0.1},
)

# MMR（课例最终用于 RAG：偏事实问答）
retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 3, "fetch_k": 20, "lambda_mult": 1},
)
```

| `lambda_mult` | 倾向 |
| --- | --- |
| **偏大（如 1）** | 更抓最相似 → 事实问答 |
| **偏小** | 更多样 → 摘要 / 概览 |

也可在 `search_kwargs` 里加 `filter` 按 metadata 过滤（如某 `source`）。

---

## 4. RAG Prompt + LCEL 链

### 4.1 Prompt

旧版可 `hub.pull("rlm/rag-prompt")`；LangChain v1 课例改为**本地模板**（Hub 可不用）：

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = """You are an assistant for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know.
Use three sentences maximum and keep the answer concise.

Question: {question}
Context: {context}

Answer:"""

prompt = ChatPromptTemplate.from_template(prompt)
```

占位符：`{context}`（检索拼好的文本）、`{question}`（用户问题）。

### 4.2 `format_docs` + `RunnablePassthrough`

Retriever 返回 `List[Document]`，Prompt 要的是**字符串**：

```python
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)
```

问题要同时进「检索」和「Prompt」：字典映射 + 透传：

```text
question（字符串）
  ├─ retriever | format_docs  → context
  └─ RunnablePassthrough()    → question
       ↓
  prompt → llm → StrOutputParser
```

### 4.3 完整链

```python
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

llm = ChatOllama(model="qwen3", base_url="http://localhost:11434")

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

print(rag_chain.invoke("how to lose weight?"))
print(rag_chain.invoke("how to gain muscle mass?"))
```

一次 `invoke(question)`：自动检索 → 填模板 → 生成答案。

---

## 5. 调参经验

同一 Retriever，**改 Prompt 往往比只改 k 更明显**。

| 方向 | 做法 |
| --- | --- |
| 原模板过短 | `three sentences maximum` 易拒答或过泛 |
| 加强 context-only | 加 *answered from the context only* / *relevant to the question* |
| 结构化输出 | 改成 *Answer in bullet points* |
| 检索 | 事实问答：MMR + `lambda_mult=1`；摘要：调小 `lambda_mult` |
| 阈值 | `score_threshold` 过高 → 无文档；过低 → 噪声 |

调参 checklist：

```text
检索：search_type / k / fetch_k / lambda_mult / score_threshold
Prompt：长度 / 格式 / 是否强制 context-only
LLM：model、temperature 等
```

私有数据慎开 LangSmith（会上传 trace）；本地 FAISS + Ollama 默认不出本机。

---

## 文末实践代码

```python
import os
import warnings
from dotenv import load_dotenv

os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
warnings.filterwarnings("ignore")
load_dotenv()

from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# 1) 加载库（路径按你的落盘位置改）
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434",
)
vector_store = FAISS.load_local(
    r"..\09. Vector Stores and Retrievals\health_supplements",
    embeddings,
    allow_dangerous_deserialization=True,
)

# 2) Retriever（课例：MMR）
retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 3, "fetch_k": 20, "lambda_mult": 1},
)

# 3) Prompt + LLM + 链
prompt = ChatPromptTemplate.from_template(
    """You are an assistant for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know.
Use three sentences maximum and keep the answer concise.

Question: {question}
Context: {context}

Answer:"""
)
llm = ChatOllama(model="qwen3", base_url="http://localhost:11434")


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

for q in ["how to lose weight?", "how to gain muscle mass?"]:
    print("Q:", q)
    print("A:", rag_chain.invoke(q), "\n")
```
