---
title: Vector Stores and Retrievals
aliases:
  - 向量存储与检索
  - Chat My PDF
  - FAISS
  - RAG Vector Store
created: 2026-07-27
updated: 2026-08-01
series: 本地 RAG
part: 9
source: Vector Stores and Retrievals.ipynb（可删）· 字幕 108–115（可删）
tags:
  - type/literature-note
  - topic/rag
  - topic/faiss
  - topic/langchain
  - topic/ollama
  - topic/embedding
  - topic/local-rag
  - status/draft
---

# Vector Stores and Retrievals（向量存储与检索）

> [!summary]
> **本地 RAG · 第 9 部分 · Chat My PDF**。PDF → **RecursiveCharacterTextSplitter** 分块 → **Ollama `nomic-embed-text`** 嵌入 → **FAISS** 入库与相似度检索。本节做到「取出相关 chunk」；把 chunk + 问题交给 LLM 生成答案在下一模块。

数据：<https://github.com/laxmimerit/rag-dataset>（健身 / 健康补剂 PDF）

## 本章目录

| 章节 | 学什么 |
| --- | --- |
| §1 RAG 两阶段 | 入库 vs 检索生成；为何必须分块 |
| §2 FAISS / Chroma | 选型与 Windows 环境 |
| §3 加载 PDF | `PyMuPDFLoader` + `os.walk` |
| §4 分块 | `RecursiveCharacterTextSplitter`、chunk size |
| §5 Embedding | `OllamaEmbeddings`、768 维、8000 窗 |
| §6 建库与检索 | `IndexFlatL2`、`add_documents`、`search`、落盘 |
| 文末实践代码 | 对齐 notebook 全流程 |

---

## 1. RAG 两阶段

![[09-vector-cell3-0.png]]

| 模块 | 做什么 | 本节 |
| --- | --- | --- |
| **① 入库** | PDF → chunk → embedding → 向量库 | ✅ |
| **② 检索 + 生成** | 问题 → embedding → Top-K chunk → LLM → 增强回答 | 后续 |

```text
入库：
Documents → Extract Text → Chunks → Ollama Embedding → FAISS

检索生成：
Question → Embedding → Similarity Search → Top-K chunks
       → chunks + Question → LLM → Final Answer
```

### 为何不能整库塞进 LLM

接 Document Loaders：长上下文有**灾难性遗忘**——更易抓住首尾、丢掉中间。即便窗口约 **128K**，正式 RAG 仍用**小块 + 检索**，只喂相关片段。

| 约束 | 含义 |
| --- | --- |
| LLM 窗口 | 不宜整本硬塞 |
| Embedding 窗口 | `nomic-embed-text` 仅约 **8000** tokens，单 chunk 不可超 |

入库与检索必须用**同一套** embedding 模型，维度才对齐。

---

## 2. FAISS vs Chroma 与环境

| | FAISS | Chroma |
| --- | --- | --- |
| 来源 | Facebook AI Similarity Search | Chroma |
| 安装 | `pip install faiss-cpu` | `langchain-chroma` 等 |
| Windows | 课程首选，坑较少 | 常撞编译器 / VS |
| 建库 | 常先建 `faiss.Index*` 再包进 `FAISS(...)` | 一般不用手写 index |
| 入库 / 检索 | `add_documents`、similarity search | 流程基本相同 |

```bash
pip install faiss-cpu
# 另需：langchain-community langchain-text-splitters langchain-ollama pymupdf tiktoken python-dotenv
ollama pull nomic-embed-text
```

```python
import os
import warnings
from dotenv import load_dotenv

os.environ["KMP_DUPLICATE_LIB_OK"] = "True"  # Windows 上 FAISS+Chroma 同机时常见
warnings.filterwarnings("ignore")  # 演示用
load_dotenv()  # 可选 LangSmith
```

---

## 3. 加载全部 PDF

```python
from langchain_community.document_loaders import PyMuPDFLoader
import os

pdfs = []
for root, dirs, files in os.walk("rag-dataset"):
    for file in files:
        if file.endswith(".pdf"):
            pdfs.append(os.path.join(root, file))

docs = []
for pdf in pdfs:
    docs.extend(PyMuPDFLoader(pdf).load())  # 按页 → Document

len(docs)  # notebook：64
```

| 要点 | 说明 |
| --- | --- |
| `docs` | `list[Document]`，可直接 `split_documents` |
| 与手写 `chunk_text` | 本节改用官方 splitter，吃 Document 列表 |

`rag-dataset` 放在与 notebook 同级目录。

---

## 4. 分块：`RecursiveCharacterTextSplitter`

按分隔符递归切（段 → 句 → 字符），是 LangChain 最常用分块器。

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,    # 字符（不是 token）
    chunk_overlap=100,  # 边界重叠，减轻断句丢语义
)
chunks = text_splitter.split_documents(docs)

enc = tiktoken.encoding_for_model("gpt-4o-mini")  # 仅计数参考
len(enc.encode(chunks[0].page_content))  # 例：294
len(enc.encode(chunks[1].page_content))  # 例：219
len(enc.encode(docs[1].page_content))    # 整页例：~922
```

| 项目 | notebook / 课程 |
| --- | --- |
| 页数 | 64 |
| 块数 | 约 **311**（口述有时说 ~321，以跑数为准） |
| 每块 token | 约 200–300 |
| 整页 token | 约 1000 |

### 怎么选 chunk size

| 文本形态 | 建议 |
| --- | --- |
| 信息密、一页多主题（科研/综述） | **偏小**，检索更准 |
| 按章/节组织的长文 | 可按 section 切，块可更大 |
| 硬上限 | 单块 < embedding 窗口（8000） |

口述量级「4000–5000 字符 / 1000–2000 tokens」是「宜小」的参考；**实操以 notebook 的 1000/100 为准**做实验。

---

## 5. Embedding：`OllamaEmbeddings`

```python
from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434",
)

vector = embeddings.embed_query("Hello World")
len(vector)  # 768
```

| 项 | 课程口径 |
| --- | --- |
| 模型 | `nomic-embed-text`（先 `ollama pull`） |
| 参数量 | 约 137M，FP16 |
| 上下文 | **8000** tokens |
| 维度 | **768** |

短文本用 `embed_query`；批量进库由 `vector_store.add_documents` 内部调用。

---

## 6. 建 FAISS、检索、落盘

```python
import faiss
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore

index = faiss.IndexFlatL2(len(vector))  # L2；初始 ntotal=0, d=768

vector_store = FAISS(
    embedding_function=embeddings,
    index=index,
    docstore=InMemoryDocstore(),
    index_to_docstore_id={},
)

ids = vector_store.add_documents(documents=chunks)
len(ids), vector_store.index.ntotal  # notebook：(311, 311)
```

| 对象 | 作用 |
| --- | --- |
| `IndexFlatL2` | 暴力 L2 近邻（小库够用） |
| `InMemoryDocstore` | 存原文 Document |
| `index_to_docstore_id` | FAISS 行号 ↔ doc id |
| `add_documents` | 自动 embedding + 写入 |

### 检索（先取 chunk）

```python
question = "how to gain muscle mass?"
hits = vector_store.search(
    query=question,
    k=5,
    search_type="similarity",
)
# hits：最多 5 条相关 Document（含 metadata.source 等）
```

问题会在内部被 embedding，再与库中向量比相似度。

### 持久化

```python
db_name = "health_supplements"
vector_store.save_local(db_name)
# → health_supplements/index.faiss + index.pkl
# 下次：FAISS.load_local(db_name, embeddings, allow_dangerous_deserialization=True)
```

> [!note]
> `load_local` 的 `allow_dangerous_deserialization` 因 pickle 安全策略；只加载自己信任的库。

---

## 数字速查

| 项目 | 数值 |
| --- | --- |
| PDF 页 | 64 |
| chunks | ~311 |
| chunk_size / overlap | 1000 / 100 字符 |
| embedding 维 | 768 |
| nomic 上下文 | 8000 tokens |
| 检索 k | 5 |
| Ollama | `http://localhost:11434` |

---

## 文末实践代码

```python
import os
import warnings
from dotenv import load_dotenv

os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
warnings.filterwarnings("ignore")
load_dotenv()

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
import faiss

# 1) 加载 PDF
pdfs = []
for root, dirs, files in os.walk("rag-dataset"):
    for file in files:
        if file.endswith(".pdf"):
            pdfs.append(os.path.join(root, file))

docs = []
for pdf in pdfs:
    docs.extend(PyMuPDFLoader(pdf).load())

# 2) 分块
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
chunks = text_splitter.split_documents(docs)

# 3) Embedding + FAISS
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434",
)
dim = len(embeddings.embed_query("Hello World"))
index = faiss.IndexFlatL2(dim)

vector_store = FAISS(
    embedding_function=embeddings,
    index=index,
    docstore=InMemoryDocstore(),
    index_to_docstore_id={},
)
vector_store.add_documents(documents=chunks)

# 4) 检索
hits = vector_store.search(
    query="how to gain muscle mass?",
    k=5,
    search_type="similarity",
)
for d in hits:
    print(d.metadata.get("source"), d.page_content[:200], "...\n")

# 5) 落盘
vector_store.save_local("health_supplements")
```
