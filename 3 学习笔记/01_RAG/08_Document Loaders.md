---
title: Document Loaders
aliases:
  - 文档加载器
  - PyMuPDFLoader
  - WebBaseLoader
  - MarkItDown
  - Docling
created: 2026-07-25
updated: 2026-08-01
series: 本地 RAG
part: 8
source: 08. Document Loaders（1–5 notebook 可删）· 字幕 075–107（可删）
tags:
  - type/literature-note
  - topic/langchain
  - topic/document-loader
  - topic/rag
  - topic/ollama
  - topic/local-rag
  - topic/markitdown
  - topic/docling
  - status/draft
---

# Document Loaders（PDF / Web / Office / MarkItDown / Docling）

> [!summary]
> **本地 RAG · 第 8 部分**。把各类文件变成文本 context，再交给 `ChatOllama` 做问答 / 摘要 / 报告。本课多数是 **整段塞进上下文**（尚未向量检索）。选型：PDF 用 **PyMuPDF**；网页用 **WebBaseLoader + 清洗分块**；Office 用 **Unstructured / Docx2txt**；快速转 MD 用 **MarkItDown**；复杂 PDF/扫描/表格图用 **Docling**。

官方加载器列表：<https://docs.langchain.com/oss/python/integrations/document_loaders>  
默认 LLM：`ChatOllama(base_url="http://localhost:11434", model="qwen3")`（见 `scripts/llm.py`）。

## 本章目录

| 章节 | 学什么 |
| --- | --- |
| §1 总览 | 流水线、数据集、选型 |
| §2 PDF 三项目 | PyMuPDF、token、问答 / 摘要 / 报告 |
| §3 Web 新闻 | WebBaseLoader、清洗、灾难性遗忘、分块、报告 |
| §4 Office | PPT / Excel / Word + NLTK |
| §5 MarkItDown | 统一转 Markdown |
| §6 Docling | OCR、多格式导出、表与图 |
| 文末实践代码 | 各线最小可跑骨架 |

---

## 1. 总览

```text
文件 / URL
  → Document Loader（或 MarkItDown / Docling）
  → 合并 / 清洗 /（必要时）分块
  → Prompt + ChatOllama
  → 答案 / 摘要 / Markdown 报告
```

| 线 | 数据 | 策略 |
| --- | --- | --- |
| PDF | `rag-dataset` 健身补剂 PDF | 整库拼 context（约 60K tokens，需 < 模型窗口） |
| Web | 股市新闻站 URL | 清洗 → 分块逐问 → 合并 → 再生成报告 |
| Office | PPTX / XLSX / DOCX | Unstructured 或 Docx2txt → 再问 LLM |
| 转写工具 | 任意常见办公/PDF | MarkItDown（快）或 Docling（准） |

数据集（课程）：

```bash
git clone https://github.com/laxmimerit/rag-dataset.git
```

> [!note]
> 整库塞 prompt **不是**向量 RAG。窗口不够或中间段落被忽略时，才必须分块；后续课才上检索。

---

## 2. PDF：加载与三项目

### 2.1 安装与单文件

```bash
pip install pymupdf tiktoken langchain-community langchain-ollama python-dotenv
```

| 库 | 何时用 |
| --- | --- |
| **PyMuPDF**（本课主推） | 通用 PDF 文本 |
| PDFPlumber | 表格多 |
| Unstructured / 云 OCR | 多格式或扫描 |

```python
from langchain_community.document_loaders import PyMuPDFLoader

loader = PyMuPDFLoader("rag-dataset/1.pdf")  # 建议正斜杠
docs = loader.load()
# len(docs) == 页数；docs[0].page_content / .metadata（source, page, …）
```

### 2.2 目录批量 + 合并 + 估 token

```python
import os, tiktoken

def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)

pdfs = [
    os.path.join(r, f)
    for r, _, fs in os.walk("rag-dataset")
    for f in fs
    if f.lower().endswith(".pdf")
]
docs = []
for pdf in pdfs:
    docs.extend(PyMuPDFLoader(pdf).load())  # 用 extend，勿 append 整个列表

context = format_docs(docs)
enc = tiktoken.encoding_for_model("gpt-4o-mini")
print(len(enc.encode(context)))  # 课例约 60K
```

总 token 必须小于模型上下文；乱码会把 token 撑大。勿用「单页 × 页数」代替全量 encode。

### 2.3 问答链与三项目

同一 `context`，换问题 / 换 system：

```python
from langchain_ollama import ChatOllama
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain_core.output_parsers import StrOutputParser

llm = ChatOllama(base_url="http://localhost:11434", model="qwen3")

system = SystemMessagePromptTemplate.from_template(
    "You are helpful AI assistant who answer user question based on the provided context."
)
human = HumanMessagePromptTemplate.from_template(
    """Answer user question based on the provided context ONLY! If you do not know the answer, just say "I don't know".
### Context:
{context}

### Question:
{question}

### Answer:"""
)
qna_chain = ChatPromptTemplate([system, human]) | llm | StrOutputParser()

# Project 1 问答
qna_chain.invoke({"context": context, "question": "How to gain muscle mass?"})

# Project 2 摘要：换 system / prompt 为 Summarize… in {words} words

# Project 3 报告：仍用 qna_chain，question 写成
# "Provide a detailed report... Write answer in Markdown."
```

问法要贴近原文用语（如 weight loss vs reduce weight）。超出文档的内容应落到 *I don't know*。

---

## 3. Web：抓取、清洗、分块、报告

### 3.1 加载与清洗

```python
from langchain_community.document_loaders import WebBaseLoader
import re

urls = [
    "https://economictimes.indiatimes.com/markets/stocks/news",
    "https://www.livemint.com/latest-news",
    "https://www.moneycontrol.com/",
]
loader = WebBaseLoader(web_paths=urls)

docs = []
async for doc in loader.alazy_load():
    docs.append(doc)
# 同步环境也可用 loader.load()

def text_clean(text):
    text = re.sub(r"\n\n+", "\n\n", text)
    text = re.sub(r"\t+", "\t", text)
    text = re.sub(r"\s+", " ", text)
    return text

context = text_clean(format_docs(docs))
```

网页首尾常是导航/页脚，中间才是新闻。

### 3.2 灾难性遗忘 → 必须分块

即使总长未爆窗口，模型对**开头/结尾**更敏感、**中间**易丢——整页一次「Extract all news」效果差。用前 10K 字符单独问会明显更好 → 分块处理。

```python
def chunk_text(text, chunk_size=10_000, overlap=100):
    step = chunk_size - overlap
    return [text[i : i + chunk_size] for i in range(0, len(text), step)]
```

`overlap` 减轻边界截断丢语义。后续 RAG 会换 `RecursiveCharacterTextSplitter` 等。

### 3.3 可复用 `ask_llm` + 两段式报告

`scripts/llm.py`：

```python
def ask_llm(context, question):
    return qna_chain.invoke({"context": context, "question": question})
```

```python
from scripts import llm  # 按你的包路径导入

chunks = chunk_text(context)
question = "Extract stock market news from the given text."
chunk_summary = [llm.ask_llm(c, question) for c in chunks]
summary = "\n\n".join(chunk_summary)

report = llm.ask_llm(
    summary,
    "Write a detailed market news report in markdown format. Think carefully then write the report.",
)
# 写入 data/summary.md、data/report.md
```

```text
URL → WebBaseLoader → format_docs → text_clean
  → chunk_text → 逐块 ask_llm → join(summary)
  → 再 ask_llm(summary) → report.md
```

---

## 4. Office：PPT / Excel / Word

文档：<https://python.langchain.com/docs/integrations/providers/unstructured/>

```bash
pip install "unstructured[all-docs]" openpyxl python-pptx docx2txt nltk
# 或按需拆装
```

NLTK：`nltk.download("punkt")`。Windows 若报缺 **`PY3_tab`**：在 `nltk_data/tokenizers/punkt/` 下把 `PY3` **复制并改名为** `PY3_tab`，再重启 kernel。

### 4.1 PPTX → 按页 context → 演讲稿

```python
from langchain_community.document_loaders import UnstructuredPowerPointLoader

loader = UnstructuredPowerPointLoader("data/ml_course.pptx", mode="elements")
docs = loader.load()  # 按元素拆，页数 ≠ len(docs)

ppt_data = {}
for doc in docs:
    page = doc.metadata["page_number"]
    ppt_data[page] = ppt_data.get(page, "") + "\n\n" + doc.page_content

context = ""
for page, content in sorted(ppt_data.items()):
    context += f"### Slide {page}:\n\n{content.strip()}\n\n\n"

# ask_llm(context, "为每页写约 2 分钟演讲稿…") → data/ppt_script.md
```

`mode="elements"`：标题/段落等分开；图片元素通常无正文。

### 4.2 Excel：用 HTML 表，别只用纯文本

```python
from langchain_community.document_loaders import UnstructuredExcelLoader

docs = UnstructuredExcelLoader("data/sample.xlsx", mode="elements").load()
context = docs[0].metadata["text_as_html"]  # 结构化在这里
# 再 ask_llm：过滤、转 Markdown 表等；复杂统计仍应用 pandas
```

### 4.3 Word JD → 邮件

```python
from langchain_community.document_loaders import Docx2txtLoader

docs = Docx2txtLoader("data/job_description.docx").load()
context = docs[0].page_content  # 整篇一个 Document，无 mode
# ask_llm：根据 JD 写个性化求职信
```

---

## 5. MarkItDown（微软：快转 Markdown）

仓库：<https://github.com/microsoft/markitdown>

```bash
pip install "markitdown[all]"
```

```python
from pathlib import Path
from markitdown import MarkItDown

md = MarkItDown()

def convert_and_save(file_path, out_dir="markitdown"):
    file_path = Path(file_path)
    result = md.convert(file_path)
    out = Path(out_dir) / f"{file_path.stem}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(result.text_content, encoding="utf-8")
    return result

convert_and_save("data/job_description.docx")
convert_and_save("data/ml_course.pptx")
# 也可 md.convert(youtube_url) —— 多为视频描述，非字幕；易被限流
```

| 优点 | 局限 |
| --- | --- |
| 一个入口；Office 转 MD 常够用 | 复杂财报 PDF 版式/表格不稳定 |
| 快 | Windows 上音视频依赖重；YouTube 勿狂刷 |

适合批量「先变成文本」；要精保表格/扫描件 → Docling。

---

## 6. Docling（IBM：布局 / OCR / 表 / 图）

仓库：<https://github.com/docling-project/docling>

```bash
pip install docling
```

首次运行会从 Hugging Face 拉模型；有 GPU 更快。

### 6.1 转换与多格式导出

```python
from pathlib import Path
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert(Path("data/Apple-10-Q-2025-Q1.pdf"))

md = result.document.export_to_markdown()
html = result.document.export_to_html()
# 写入 docling/*.md / *.html
```

扫描 PDF 默认可走 OCR（auto / rapidocr 等）。支持 PDF、DOCX、PPTX、XLSX、HTML、图片等。

### 6.2 抽表 → CSV

```python
for i, table in enumerate(result.document.tables):
    df = table.export_to_dataframe(doc=result.document)  # 建议传 doc
    df.to_csv(f"docling/tables/table_{i+1}.csv", index=False)
```

### 6.3 抽图（需开 PDF pipeline）

```python
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption

opts = PdfPipelineOptions()
opts.generate_picture_images = True
opts.images_scale = 3.0  # 太糊可再加大

converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
)
result = converter.convert(Path("data/sample_textbook.pdf"))

for i, picture in enumerate(result.document.pictures):
    picture.get_image(result.document).save(f"docling/figures/fig_{i+1}.png")
```

不开 pipeline 时往往只有占位、无像素。默认 export MD/HTML 不一定内嵌图片文件。

| 场景 | 倾向 |
| --- | --- |
| LangChain 按页/元素进 RAG | Unstructured |
| 快速转文本/MD | MarkItDown |
| 复杂 PDF、扫描、表/图 | **Docling** |

---

## 选型速查

| 输入 | 推荐 |
| --- | --- |
| 普通 PDF 文本 | `PyMuPDFLoader` |
| 网页 | `WebBaseLoader` + `text_clean` + `chunk_text` |
| PPTX 元素级 | `UnstructuredPowerPointLoader(mode="elements")` |
| Excel 表结构 | `UnstructuredExcelLoader` → `text_as_html` |
| 简单 DOCX | `Docx2txtLoader` |
| 批量转 MD | MarkItDown |
| 扫描件 / 财报表格 / 插图 | Docling |

```text
短 context、整库可塞 → 直接 qna / summary / report
长网页、中间易丢 → 分块 ask → 汇总再报告
要向量检索 → 后续 Vector Store 课
```

---

## 文末实践代码

### A. PDF 问答骨架

```python
import os, tiktoken
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_ollama import ChatOllama
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain_core.output_parsers import StrOutputParser

def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)

docs = []
for r, _, fs in os.walk("rag-dataset"):
    for f in fs:
        if f.lower().endswith(".pdf"):
            docs.extend(PyMuPDFLoader(os.path.join(r, f)).load())

context = format_docs(docs)
print(len(tiktoken.encoding_for_model("gpt-4o-mini").encode(context)))

llm = ChatOllama(base_url="http://localhost:11434", model="qwen3")
system = SystemMessagePromptTemplate.from_template(
    "You are helpful AI assistant who answer user question based on the provided context."
)
human = HumanMessagePromptTemplate.from_template(
    """Answer based on the provided context ONLY! If you do not know, say "I don't know".
### Context:
{context}
### Question:
{question}
### Answer:"""
)
qna_chain = ChatPromptTemplate([system, human]) | llm | StrOutputParser()
print(qna_chain.invoke({"context": context, "question": "How to gain muscle mass?"}))
```

### B. Web 分块报告骨架

```python
import re, os
from langchain_community.document_loaders import WebBaseLoader
# from scripts.llm import ask_llm  # 或内联 qna_chain

def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)

def text_clean(text):
    text = re.sub(r"\n\n+", "\n\n", text)
    text = re.sub(r"\t+", "\t", text)
    text = re.sub(r"\s+", " ", text)
    return text

def chunk_text(text, chunk_size=10_000, overlap=100):
    step = chunk_size - overlap
    return [text[i : i + chunk_size] for i in range(0, len(text), step)]

loader = WebBaseLoader(web_paths=["https://www.moneycontrol.com/"])
docs = loader.load()
context = text_clean(format_docs(docs))
chunks = chunk_text(context)
# summaries = [ask_llm(c, "Extract stock market news from the given text.") for c in chunks]
# summary = "\n\n".join(summaries)
# report = ask_llm(summary, "Write a detailed market news report in markdown format.")
# os.makedirs("data", exist_ok=True)
# open("data/report.md", "w", encoding="utf-8").write(report)
```

### C. Docling 转 MD + 表

```python
from pathlib import Path
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
path = Path("data/Apple-10-Q-2025-Q1.pdf")
result = converter.convert(path)
path.with_suffix(".md").write_text(
    result.document.export_to_markdown(), encoding="utf-8"
)
for i, table in enumerate(result.document.tables):
    table.export_to_dataframe(doc=result.document).to_csv(
        f"table_{i+1}.csv", index=False
    )
```
