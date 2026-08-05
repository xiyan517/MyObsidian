---
title: Resume Parsing with LLM
aliases:
  - 简历解析
  - Resume Parser
  - Streamlit Resume
created: 2026-08-03
updated: 2026-08-03
series: 本地 RAG
part: 15
source: 原 16. Resume Parsing 已并入本文（notebook / scripts / app 可删）
tags:
  - type/literature-note
  - topic/resume
  - topic/llm
  - topic/streamlit
  - topic/json
  - topic/local-rag
  - status/draft
---

# Resume Parsing with LLM

> [!summary]
> **本地 RAG · 第 15 部分**。用 **LLM + 专用 prompt** 把任意版式 PDF 简历抽成统一 JSON（可入库）。核心是两步链：`ask_llm`（`StrOutputParser`）→ `validate_json`（`JsonOutputParser`）。notebook 用 `PyMuPDFLoader` 批跑；Streamlit 直连 `pymupdf` 上传解析。换应用时主要改 prompt，骨架可复用。

```bash
pip install python-dotenv pymupdf langchain-community langchain-ollama langchain-core streamlit
# Ollama 需已拉取模型，例如：ollama pull qwen3
```

Streamlit 入门（课上播放列表）：<https://www.youtube.com/watch?v=hff2tHUzxJM&list=PLc2rvfiptPSSpZ99EnJbH5LjTJ_nOoSWW>

## 本章目录

| 章节 | 学什么 |
| --- | --- |
| §1 目标与流程 | 为何用 LLM、JSON 产物、总流程 |
| §2 推荐目录 | 删源码后如何自建工程 |
| §3 读 PDF | Loader vs 直连 PyMuPDF |
| §4 `scripts/llm.py` | 完整模块：prompt、两步链 |
| §5 notebook 批跑 | context / question → 落盘 |
| §6 Streamlit | 上传 → Parse → 展示 |
| 文末实践代码 | `llm.py` + notebook 脚本 + `app.py` |

---

## 1. 目标与流程

以前常用 **spaCy / Transformers** 流水线；现在用 LLM 即可，关键是：

| 关键 | 说明 |
| --- | --- |
| **选对模型** | 小模型结构化弱；仓库默认 `qwen3`，备用 `qwen2.5:7b`（同 [[14_LinkedIn Profile Scraping]]） |
| **写对 prompt** | 字段 schema +「合法 JSON、不要开场白」 |
| **两步输出** | 先抽成文本，再校验成真正 JSON |

与 LinkedIn 课同一类问题：非结构化文本 → LLM → 结构化 JSON；差别是来源为 **PDF 简历** 而非网页。

```text
PDF 简历
   │
   ├─ notebook: PyMuPDFLoader → page_content
   └─ Streamlit: pymupdf.open(stream=…) → 逐页 get_text
   │
   ▼
context + question
   │
   ▼
ask_llm  ──StrOutputParser──► 可能带杂质的「类 JSON」
   │
   ▼
validate_json ──JsonOutputParser──► dict
   │
   ├─ parsed_resume/*.json（notebook）
   ├─ 页面展示 / 复制（Streamlit）
   └─ 自写入 MySQL / MongoDB / DynamoDB 等
```

示例产物形态：

```json
{
  "Contact Information": {
    "Name": "Kumar Pallav",
    "Email": "me@kumarpallav.com",
    "Phone Number": "+1-206-910-0006",
    "Website/Portfolio": "http://kumarpallav.com"
  },
  "Education": {
    "Institution Name": "Indian Institute of Technology, Bombay",
    "Degree": "Bachelor of Computer Science and Engineering (with Hons.)",
    "Field of Study": "Computer Science and Engineering",
    "Graduation Dates": "Jun 2010 - May 2014"
  },
  "Experience": [{ "Job Title": "...", "Company Name": "...", "...": "..." }],
  "Projects": [{ "...": "..." }],
  "Skills": { "Programming Languages": [], "Technologies/Tools": [] }
}
```

环境变量（LangSmith 等）便于观察调用：

```python
from dotenv import load_dotenv
load_dotenv("./../.env")  # 或 load_dotenv()，视工作目录而定
```

---

## 2. 推荐目录（删课包后自建）

原课在 `16. Resume Parsing/`。删掉 notebook / scripts / app 后，可按下面自建：

```text
resume_parsing/
├── .env                    # 可选：LangSmith 等
├── resume/                 # 放入 *.pdf（自备或原课样例）
├── parsed_resume/          # notebook 落盘 JSON
├── scripts/
│   ├── __init__.py         # 空文件即可（使 scripts 成为包）
│   └── llm.py              # §4 / 文末完整代码
├── run_notebook.py         # 可选：§5 批跑逻辑
└── app.py                  # §6 Streamlit
```

| 部件 | 作用 |
| --- | --- |
| `scripts/__init__.py` | **空文件**；没有它则 `from scripts.llm import …` 可能失败 |
| `scripts/llm.py` | notebook 与 Streamlit **共用** |
| `resume/` / `parsed_resume/` | 输入 PDF / 输出 JSON |

运行 Streamlit 前 `cd` 到含 `scripts/` 与 `app.py` 的目录：

```bash
streamlit run app.py   # http://localhost:8501
```

---

## 3. 读 PDF：两种方式

| 场景 | 方式 | 说明 |
| --- | --- | --- |
| 批跑 / notebook | `PyMuPDFLoader` | LangChain 封装，底层仍是 PyMuPDF |
| Streamlit 上传 | `import pymupdf` | 从**字节流**打开，无磁盘路径 |

```python
# --- notebook / 脚本 ---
from langchain_community.document_loaders import PyMuPDFLoader

filename = "resume-1.pdf"  # 课上也可先用较短的 resume-2.pdf
loader = PyMuPDFLoader("resume/{}".format(filename))
docs = loader.load()
context = docs[0].page_content

# --- Streamlit 上传 ---
import pymupdf

bytearray = uploaded_file.read()
pdf = pymupdf.open(stream=bytearray, filetype="pdf")  # filetype 不是文件名
context = ""
for page in pdf:
    context = context + "\n\n" + page.get_text()
pdf.close()
```

多页简历必须拼页；页间用 `\n\n` 隔开。

---

## 4. `scripts/llm.py`（核心）

相对本系列旧版「问答」脚本：

| 部分 | 变化 |
| --- | --- |
| `ChatOllama` / `system` | 基本不变 |
| 多 `JsonOutputParser` | 第二步用（见 [[05_Output Parsing]]） |
| Human prompt | **按简历字段重写**（换应用主要改这里） |
| 两个函数 | 链组在函数**内部** |

设计要点：

- ① `StrOutputParser`：第一步直接 `JsonOutputParser` 课上实测不稳  
- ② 再 `validate_json`：去掉开场白 / 修非法 JSON  
- 可改成校验失败则循环（上限 5–6 次）；课上固定两步  

完整模块见文末；逻辑摘要：

```python
# ask_llm: template | llm | StrOutputParser
#   invoke({"context": context, "question": question})

# validate_json: template | llm | JsonOutputParser
#   invoke({"data": data})
```

抽取 prompt 要求的字段：Contact / Education / Experience / Projects / Skills / Additional Information。  
`{question}` 再塞任务句，例如「抽成合法 JSON、不要 preamble」。

模型（仓库现状）：

```python
model = "qwen3"
# model = "qwen2.5:7b"  # 复杂简历或输出不对时改用
```

---

## 5. notebook 批跑：抽取 → 校验 → 落盘

```python
question = """You are tasked with parsing a job resume. Your goal is to extract relevant information in a valid structured 'JSON' format.
                Do not write preambles or explanations."""

# 必须 scripts.llm，不能 from scripts import ask_llm（函数不在包根）
from scripts.llm import ask_llm, validate_json

response = ask_llm(context=context, question=question)
# 常「像 JSON」但含杂质 → 非法
response = validate_json(response)

import json
output_file = "parsed_resume/{}".format(filename.replace(".pdf", ".json"))
json.dump(response, open(output_file, "w"), indent=4)
# resume-1.pdf → parsed_resume/resume-1.json
```

对照 PDF 核对 Name / Email / Education / Experience 等。换文件只改 `filename` 重跑。输出不对 → 回 `llm.py` 换强模型。

---

## 6. Streamlit：上传 → Parse Resume → 展示

界面：标题 → 上传 → **Parse Resume** → 双 spinner → JSON + `st.balloons()`。

| 步骤 | UI | 调用 |
| --- | --- | --- |
| ① | Parsing Resume… | `ask_llm` |
| ② | Validating JSON… | `validate_json`（约再十余秒） |
| ③ | Extracted Information | `st.write(response)`，可复制入库 |

注意：`question` / 按钮逻辑在上传块之外时，须先上传生成 `context` 再点按钮；未上传就点会 `NameError`。完整 `app.py` 见文末。

> [!warning]
> 复杂简历若格式不对，换更强本地模型。本地 LLM 吃算力；流程本身是上传 → 两步 LLM → JSON。

---

## 文末实践代码（可替代原课文件）

以下三块分别对应可删除的 `scripts/llm.py`、notebook、`app.py`。先建好 §2 目录，`ollama pull qwen3`（或 `qwen2.5:7b`）。

### A. `scripts/__init__.py`

空文件。

### B. `scripts/llm.py`

```python
from langchain_ollama import ChatOllama
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

base_url = "http://localhost:11434"
model = "qwen3"
# model = "qwen2.5:7b"

llm = ChatOllama(base_url=base_url, model=model)

system = SystemMessagePromptTemplate.from_template(
    """You are helpful AI assistant who answer user question based on the provided context."""
)

prompt = """
            **Task:** Extract key information from the following resume text.

            **Resume Text:**
            {context}

            **Instructions:**
            Please extract the following information and format it in a clear structure:

            1. **Contact Information:**
            - Name:
            - Email:
            - Phone Number:
            - Website/Portfolio:

            2. **Education:**
            - Institution Name:
            - Degree:
            - Field of Study:
            - Graduation Dates:

            3. **Experience:**
            - Job Title:
            - Company Name:
            - Location:
            - Dates of Employment:
            - Responsibilities/Projects:

            4. **Projects:**
            - Project Title:
            - Description/Technologies Used:
            - Outcomes/Results:

            5. **Skills:**
            - Programming Languages:
            - Technologies/Tools:

            6. **Additional Information:** (if applicable)
            - Certifications:
            - Awards or Honors:
            - Professional Affiliations:
            - Languages:

            **Question:**
            {question}

            **Extracted Information:**
        """

prompt = HumanMessagePromptTemplate.from_template(prompt)


def ask_llm(context, question):
    messages = [system, prompt]
    template = ChatPromptTemplate(messages)
    qna_chain = template | llm | StrOutputParser()
    return qna_chain.invoke({"context": context, "question": question})


def validate_json(data):
    json_prompt = """
            Please validate and correct the following JSON data:

            **Extracted Information:**
            {data}

            Provide only the corrected JSON, with no preamble or explanation.

            **Corrected JSON:**"""

    json_prompt = HumanMessagePromptTemplate.from_template(json_prompt)
    json_messages = [system, json_prompt]
    json_template = ChatPromptTemplate(json_messages)
    json_chain = json_template | llm | JsonOutputParser()
    return json_chain.invoke({"data": data})
```

### C. 批跑脚本（原 notebook）

在含 `scripts/`、`resume/`、`parsed_resume/` 的目录执行：

```python
import json
from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from scripts.llm import ask_llm, validate_json

load_dotenv("./../.env")  # 按实际路径调整

filename = "resume-1.pdf"
# filename = "resume-2.pdf"

docs = PyMuPDFLoader("resume/{}".format(filename)).load()
context = docs[0].page_content

question = """You are tasked with parsing a job resume. Your goal is to extract relevant information in a valid structured 'JSON' format.
                Do not write preambles or explanations."""

response = ask_llm(context=context, question=question)
response = validate_json(response)

output_file = "parsed_resume/{}".format(filename.replace(".pdf", ".json"))
json.dump(response, open(output_file, "w"), indent=4)
print(response)
```

### D. `app.py`

```python
# Streamlit Application Video and Playlist
# https://www.youtube.com/watch?v=hff2tHUzxJM&list=PLc2rvfiptPSSpZ99EnJbH5LjTJ_nOoSWW

import streamlit as st
import pymupdf
from scripts.llm import ask_llm, validate_json

st.title("Resume Parsing")
st.write("Upload a resume in PDF format to extract information")

uploaded_file = st.file_uploader("Choose a file")

if uploaded_file is not None:
    bytearray = uploaded_file.read()
    pdf = pymupdf.open(stream=bytearray, filetype="pdf")
    context = ""
    for page in pdf:
        context = context + "\n\n" + page.get_text()
    pdf.close()

question = """You are tasked with parsing a job resume. Your goal is to extract relevant information in a valid structured 'JSON' format.
                Do not write preambles or explanations."""

if st.button("Parse Resume"):
    with st.spinner("Parsing Resume..."):
        response = ask_llm(context=context, question=question)
    with st.spinner("Validating JSON..."):
        response = validate_json(response)
    st.write("**Extracted Information**")
    st.write(response)
    st.write("You can copy the JSON output and use it in your application.")
    st.balloons()
```

```bash
streamlit run app.py
```

---

## 相关笔记

- [[14_LinkedIn Profile Scraping]] — 网页 → 两轮 LLM 结构化（同类「脏文本 → JSON」）
- [[10_Chat with Your Own Documents]] — Document loader / PDF；旧版 LLM 脚本对照
- [[11_Tool Calling]] — 同类脚本复用思路
- [[05_Output Parsing]] — `StrOutputParser` / `JsonOutputParser`
