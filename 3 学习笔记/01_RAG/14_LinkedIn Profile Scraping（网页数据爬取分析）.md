---
title: LinkedIn Profile Scraping
aliases:
  - LinkedIn Scraper
  - LinkedIn + LLM
  - Selenium LinkedIn
created: 2026-07-29
updated: 2026-08-03
series: 本地 RAG
part: 14
source: 课程视频 SQtwhuYJk3M · 原 notebook 已并入本文（可删）
tags:
  - type/literature-note
  - topic/linkedin
  - topic/selenium
  - topic/beautifulsoup
  - topic/llm
  - topic/web-scraping
  - topic/local-rag
  - status/draft
---

# LinkedIn Profile Scraping（Selenium + LLM）

> [!summary]
> **本地 RAG · 第 14 部分**。LinkedIn 必须登录才能看 Profile；用 **Selenium** 登录并取源码，**BeautifulSoup** 只切 **`main` → section**，清洗后交给 **LLM 两轮抽取**（分块 → 按 schema 合并）。字段级解析不依赖易变 class，DOM 改版时仍可复用同一套路。

依赖：

```bash
pip install python-dotenv selenium beautifulsoup4 lxml langchain-ollama langchain-core
```

视频：<https://youtu.be/SQtwhuYJk3M>  
演示 Profile（跟练请先固定此 URL）：`https://www.linkedin.com/in/laxmimerit`

## 本章目录

| 章节 | 学什么 |
| --- | --- |
| §1 为何难、为何用 LLM | 登录墙、只要 main、抗 class 变更 |
| §2 目标与流程 | Selenium → 切块 → 两轮 LLM → JSON |
| §3 工具速览 | WebDriver、By、BeautifulSoup |
| §4 环境与登录 | `.env`、填表、验证码、固定 URL |
| §5 解析 Profile | page_source、锁定 main、按 card 切块 |
| §6 清洗与去重 | 正则收空白、对折半段去重 |
| §7 第一轮 LLM | `ask_llm`、section keys、换 Qwen、全量抽取 |
| §8 第二轮 LLM | 检视 responses、按 schema 合并 |
| §9 可推广性与注意 | 职位页 / 登录墙站点、风控 |
| 文末实践代码 | 完整可跑骨架（可替代原 notebook） |

---

## 1. 为何难、为何用 LLM

相对公开页爬虫，LinkedIn Profile **必须邮箱 + 密码**：

| 情况 | 结果 |
| --- | --- |
| 无痕 / 未登录打开 Profile | 弹出登录；**看不到**资料正文 |
| 此时 parse HTML | **拿不到** Profile 数据 |
| 登录后 | 才出现完整资料页 |

因此需要 **Selenium**（或同类浏览器自动化）完成登录，再取 `page_source`。

### 1.1 只要资料区，不要整页

登录后真正资料在中间 **`main`** 里：

- **要**：`main` 内各 `section`（About、Experience、Education …）
- **不要**：右侧边栏、推荐、其它无关 div

侧栏一并喂给 LLM → 易被干扰。DevTools：右键检查，悬停 `main` 应高亮整块资料区。

### 1.2 经典硬解析 vs LLM

| 做法 | 思路 | 痛点 |
| --- | --- | --- |
| 经典硬解析 | 按 class / 结构逐字段取 | LinkedIn class 常带随机串且会变 → 易碎 |
| **本课：LLM** | 先拿到 `main` 文本，再按语义抽字段 | 少依赖易变 class；容器定位仍可能短暂靠 class |

> [!note]
> 另有「不用 LLM 的经典 LinkedIn 抓取」路线（细粒度 JSON、实现成本高）。本课目标是**可读结构化字段**，不是复刻那套细 JSON。定位 `main` / `section` 的 class 失效时用 Inspect 重找，**字段级解析交给 LLM**。

---

## 2. 目标与流程

```text
Selenium 登录（EMAIL + PASSWORD）
        │
        ▼
打开目标 Profile · 取 page_source
        │
        ▼
只取 main → section 切块（忽略侧栏）
        │
        ▼
clean_text · remove_duplicates
        │
        ▼
LLM ①：逐区块抽取 → responses（可落盘 JSON）
        │
        ▼
LLM ②：按 schema 合并 → Name / Headline / About / …
```

| 组件 | 作用 |
| --- | --- |
| **Selenium** | 登录；驱动浏览器；取需认证页源码 |
| **BeautifulSoup** | 从 HTML 切出 `main` / `section`，再 `get_text` |
| **LLM（两轮）** | ① 分块抽取 ② 按 schema 合并成干净结构 |

---

## 3. 工具速览

文档：[selenium.dev](https://www.selenium.dev/) → Documentation（浏览器自动化；非 Selenium IDE）。本课只用最小子集。

### 3.1 Selenium

| 能力 | 本课用法 |
| --- | --- |
| WebDriver | `driver = webdriver.Chrome()` |
| 打开页 | `driver.get(url)` |
| 定位 | `find_element(By.ID, …)` 填邮箱密码并 `submit` |

登录框优先用稳定 **ID**（`username` / `password`），比 class 抗变。

> [!warning] 必须自核的两个 class
> LinkedIn **内部** class 常变，课上字符串**不保证**本地仍有效。本课不靠细碎 class 抽字段，但这两个容器要在 DevTools 核对：
>
> 1. **`main` 主资料区** class  
> 2. **卡片 `section`** class（课上为 `artdeco-card`）
>
> 其它内部 class 变了可不管。

### 3.2 BeautifulSoup

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(page_source, "lxml")
# 锁定 main 后：对各 section.get_text()
```

分工：Selenium 拿 HTML → BeautifulSoup 切块成文本 → LLM。

---

## 4. 环境与登录

### 4.1 凭证与限额

`.env`（勿提交仓库）：

```env
EMAIL=your@email.com
PASSWORD=your_password
```

用**你自己**的账号登录后，才能打开并抓取其它人的 Profile。

> [!warning] 抓取限额
> LinkedIn 可能封号或限流。公开额度不固定；课上经验：**一天别超过约 5200 次**。仅教学跟练，勿批量狂刷。

### 4.2 启动并登录

```python
import os
import re
import json
import warnings
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

warnings.filterwarnings("ignore")
load_dotenv()

driver = webdriver.Chrome()  # 提示「由自动测试软件控制」属正常
driver.get("https://www.linkedin.com/login")
# driver.title → 'LinkedIn Login, Sign in | LinkedIn'

email = driver.find_element(By.ID, "username")
email.send_keys(os.getenv("EMAIL"))

password = driver.find_element(By.ID, "password")
password.send_keys(os.getenv("PASSWORD"))
password.submit()
```

> [!note]
> **首次登录**可能弹出验证码，手动过一次即可；同会话内一般可继续自动化。

### 4.3 打开固定 Profile

结构易变；跟课先用固定 URL，学会流程后再换人：

```python
# MAKE SURE TO USE ONLY THIS URL TO AVOID BEING STUCK IN ERRORS
url = "https://www.linkedin.com/in/laxmimerit"
driver.get(url)
```

资料以多张 card / `section` 呈现，常为动态填充。本课**不**覆盖：点进子链接再深入抓取。

---

## 5. 解析 Profile

### 5.1 取源码 → 为何必须切块

```python
page_source = driver.page_source  # 很大
soup = BeautifulSoup(page_source, "lxml")
# soup.get_text() 整页仍太大，且混侧栏噪音
```

整页丢给 ChatGPT / 本地 LLM → 常报数据过大。若模型能一口吞整页，流程可退化成「拿 source → 调 LLM」；现实不行，必须**缩小范围、一次一小块**。

### 5.2 锁定 `main`，再按 section 切

class **务必在 DevTools 自核**（下列字符串为录课时快照，本地可能已变）：

```python
profile = soup.find("main", {"class": "IDbhLWzXdzKoCEksNaayQTAEeGRjvNDI"})
# profile.get_text() → 基本是本人资料；侧栏被排除

sections = profile.find_all("section", {"class": "artdeco-card"})
len(sections)  # 课上约 17–20（含 Languages / Interests / Courses 等小块）

sections_text = [section.get_text() for section in sections]
```

> [!tip]
> 单块（如 About）可贴进 ChatGPT 做摘要验证「切块有效」；整页不行。再换成本地 Ollama（§7）。

### 5.3 文本为何会「同一句出现两遍」

LinkedIn 常同时有**可见文案** + **无障碍隐藏文案** → `get_text()` 抓到两份。§6 清洗。

---

## 6. 清洗与去重

即便清洗后，**整包**干净文本仍可能过大 → 最终还是要**逐 section** 调 LLM。

### 6.1 `clean_text`

| 规则 | 作用 |
| --- | --- |
| `\n+` → `\n` | 连续换行收成一个 |
| `\t+` → `\t` | 连续 tab 收成一个 |
| `\t\s+` → ` ` | tab + 多空格 → 单空格 |
| `\n\s+` → `\n` | 换行后空白收掉 |

```python
def clean_text(text: str) -> str:
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"\t+", "\t", text)
    text = re.sub(r"\t\s+", " ", text)
    text = re.sub(r"\n\s+", "\n", text)
    return text


sections_text = [clean_text(s) for s in sections_text]
```

### 6.2 `remove_duplicates`（对折半段去重）

按行：若**前一半 == 后一半**，只留前半（不是严格回文）。

```python
def remove_duplicates(text: str) -> str:
    new_lines = []
    for line in text.split("\n"):
        mid = len(line) // 2
        if mid and line[:mid] == line[mid:]:
            new_lines.append(line[:mid])
        else:
            new_lines.append(line)
    return "\n".join(new_lines)


sections_text = [remove_duplicates(s) for s in sections_text]
```

---

## 7. 第一轮 LLM：按区块抽取

用本系列熟悉的 **ChatOllama + PromptTemplate + 链**。

### 7.1 `ask_llm`

```python
from langchain_ollama import ChatOllama
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain_core.output_parsers import StrOutputParser

# 解析任务用更强模型；课上可用 qwen3 或 qwen2.5:7b
llm = ChatOllama(base_url="http://localhost:11434", model="qwen3")

system = SystemMessagePromptTemplate.from_template(
    """You are helpful AI assistant who answer LinkedIn profile parsing related
    user question based on the provided profile text data."""
)


def ask_llm(prompt: str) -> str:
    """prompt 已是完整字符串（无运行时占位符）→ invoke({}) 即可。"""
    human = HumanMessagePromptTemplate.from_template(prompt)
    chain = ChatPromptTemplate([system, human]) | llm | StrOutputParser()
    return chain.invoke({})


# 冒烟：ask_llm("hello") → 带 system 的闲聊回复
```

### 7.2 `section_keys`

| 块 | key |
| --- | --- |
| `sections_text[0]` | 手写 **`Name and Headline`**（首块无清晰标题行） |
| 其余块 | 该块文本**首行**（须 `strip()`） |

```python
section_keys = ["Name and Headline"]
for section in sections_text[1:]:
    # 必须 strip：否则首行可能是空串，key 空 → 抽取对不上
    section_keys.append(section.strip().split("\n")[0])
```

课上示例 keys（随页面会变；含噪音卡，第二轮 schema 会丢掉）：

`Name and Headline` · Open to work · About · Featured · Activity · Experience · Education · Projects · Skills · Recommendations · Patents · Courses · Languages · Interests · Causes · …

> [!warning] 漏掉 `strip()`
> 打印 section 全文可能正常，但 key 列表对应项为空，LLM 等于没指定要抽什么。

`zip(section_keys, sections_text)` → 一一配对后再循环。

### 7.3 抽取模板 + 单块试跑

要点列表、最多 5 点、不要开场白。进链前用 **`.format` + `{`/`}` 翻倍**（避免被 `ChatPromptTemplate` 当占位符）。

```python
extract_template = """
Extract and return the requested information from the LinkedIn profile data in a concise, point-by-point format (up to 5 points). Avoid preambles or any additional context.

### LinkedIn Profile Data:
{}

### Information to Extract:
Extract '{}' in bullet points, limiting the output to 5 points. Provide only the necessary details.
Remember, It is LinkedIn profile data.

### Extracted Data:"""

context = sections_text[0]
k = "Name and Headline"
prompt = extract_template.format(context, k).replace("{", "{{").replace("}", "}}")
print(ask_llm(prompt))
# 例：Name / Headline / Education / Skills 等要点
```

> [!warning] 小模型不够用
> 2–3B 级 Llama 做闲聊尚可，**结构化解析偏弱**（Name/Headline 常分不开或漏抽）。全量前换成 **Qwen 2.5 7B**（约 5 GB；建议 6 GB+ 显存或较强 CPU）或其它更强本地模型：
>
> ```bash
> ollama pull qwen2.5:7b
> ```
>
> ```python
> llm = ChatOllama(base_url="http://localhost:11434", model="qwen2.5:7b")
> ```
>
> 可在 LangSmith 确认 run 已切到新模型。不必死盯某一家——当时最好的本地模型即可。

### 7.4 全量抽取并落盘

```python
responses = {}
for k, context in zip(section_keys, sections_text):
    prompt = extract_template.format(context, k).replace("{", "{{").replace("}", "}}")
    responses[k] = ask_llm(prompt)

with open("linkedin_profile_data.json", "w", encoding="utf-8") as f:
    json.dump(responses, f, indent=4, ensure_ascii=False)
# 全量约数分钟（课上约 5 分钟量级）
```

---

## 8. 第二轮 LLM：按 schema 合并

### 8.1 检视第一轮

```python
print(json.dumps(responses, indent=4, ensure_ascii=False))
```

换强模型后 Name/Headline 通常能分开。`responses` 键多且含 Open to work / Analytics 等噪音，格式也不统一 → 再加一层收束。

### 8.2 `merge_template`

按 schema 解析、纠拼写、能压缩则压缩；只要下列字段，不要开场白。

```python
merge_template = """You are provided with LinkedIn profile data in JSON format.
Parse the data according to the specified schema, correct any spelling errors,
and condense the information if possible.

### LinkedIn Profile JSON Data:
{context}

### Schema You need to follow:
You need to extract
Name:
Headline:
About:
Experience:
Education:
Skills:
Projects:
Summary:

Do not return preambles or any other information.
### Parsed Data:"""

# responses 字符串化后自带大量 { }，必须翻倍
prompt = merge_template.format(context=responses).replace("{", "{{").replace("}", "}}")
final = ask_llm(prompt)
print(final)
```

示例形态（课上最终输出）：

```json
{
  "Name": "Laxmi Kant Tiwari",
  "Headline": "Data Scientist | Gen AI in Finance & Investment Services | ...",
  "About": "...",
  "Experience": [
    {
      "Title": "Senior Manager",
      "Company": "Linedata",
      "Dates": "Sep 2024 – Present",
      "Responsibilities": ["..."]
    }
  ],
  "Education": "...",
  "Skills": "...",
  "Projects": "...",
  "Summary": "..."
}
```

| 轮次 | 作用 |
| --- | --- |
| ① | 按 DOM 切块抽 → 信息全、键多且不齐 |
| ② | 按你关心的 schema 合并、纠错、压缩 → 干净结果 |

---

## 9. 可推广性与注意

同一套路可迁移到：

- Indeed / Naukri / LinkedIn **职位页**
- 其它需要 **账号密码** 才能看内容的站点

Selenium「进得去」；只取主内容区；LLM「从脏文本抽结构」。class / DOM 再变，只要正文还在，语义抽取仍可复用。

注意：

- 频繁自动化登录可能触发风控；对自己账号负责
- 跑不通时先用 DevTools 核对 §3 里两个 class
- 本课不深入子页面链接抓取

---

## 文末实践代码（完整可跑骨架）

删除原 notebook 后，以下脚本可独立复现主流程。先写好 `.env`，并 `ollama pull qwen3`（或 `qwen2.5:7b`）。**`main` / `artdeco-card` 的 class 以你本地 DevTools 为准**，把下面两处字符串换成当前值。

```python
import os
import re
import json
import warnings
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from langchain_ollama import ChatOllama
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain_core.output_parsers import StrOutputParser

warnings.filterwarnings("ignore")
load_dotenv()

# --- 清洗 ---
def clean_text(text: str) -> str:
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"\t+", "\t", text)
    text = re.sub(r"\t\s+", " ", text)
    text = re.sub(r"\n\s+", "\n", text)
    return text


def remove_duplicates(text: str) -> str:
    new_lines = []
    for line in text.split("\n"):
        mid = len(line) // 2
        if mid and line[:mid] == line[mid:]:
            new_lines.append(line[:mid])
        else:
            new_lines.append(line)
    return "\n".join(new_lines)


# --- LLM ---
llm = ChatOllama(base_url="http://localhost:11434", model="qwen3")
# llm = ChatOllama(base_url="http://localhost:11434", model="qwen2.5:7b")

system = SystemMessagePromptTemplate.from_template(
    """You are helpful AI assistant who answer LinkedIn profile parsing related
    user question based on the provided profile text data."""
)


def ask_llm(prompt: str) -> str:
    human = HumanMessagePromptTemplate.from_template(prompt)
    chain = ChatPromptTemplate([system, human]) | llm | StrOutputParser()
    return chain.invoke({})


extract_template = """
Extract and return the requested information from the LinkedIn profile data in a concise, point-by-point format (up to 5 points). Avoid preambles or any additional context.

### LinkedIn Profile Data:
{}

### Information to Extract:
Extract '{}' in bullet points, limiting the output to 5 points. Provide only the necessary details.
Remember, It is LinkedIn profile data.

### Extracted Data:"""

merge_template = """You are provided with LinkedIn profile data in JSON format.
Parse the data according to the specified schema, correct any spelling errors,
and condense the information if possible.

### LinkedIn Profile JSON Data:
{context}

### Schema You need to follow:
You need to extract
Name:
Headline:
About:
Experience:
Education:
Skills:
Projects:
Summary:

Do not return preambles or any other information.
### Parsed Data:"""

# --- 抓取 ---
driver = webdriver.Chrome()
try:
    driver.get("https://www.linkedin.com/login")
    driver.find_element(By.ID, "username").send_keys(os.getenv("EMAIL"))
    pw = driver.find_element(By.ID, "password")
    pw.send_keys(os.getenv("PASSWORD"))
    pw.submit()
    # 若弹出验证码：此处手动完成后再继续

    driver.get("https://www.linkedin.com/in/laxmimerit")
    soup = BeautifulSoup(driver.page_source, "lxml")

    # !!! 用 DevTools 替换为当前 class !!!
    profile = soup.find("main", {"class": "IDbhLWzXdzKoCEksNaayQTAEeGRjvNDI"})
    sections = profile.find_all("section", {"class": "artdeco-card"})
    sections_text = [remove_duplicates(clean_text(s.get_text())) for s in sections]

    section_keys = ["Name and Headline"]
    for section in sections_text[1:]:
        section_keys.append(section.strip().split("\n")[0])

    responses = {}
    for k, context in zip(section_keys, sections_text):
        prompt = extract_template.format(context, k).replace("{", "{{").replace("}", "}}")
        responses[k] = ask_llm(prompt)

    with open("linkedin_profile_data.json", "w", encoding="utf-8") as f:
        json.dump(responses, f, indent=4, ensure_ascii=False)

    prompt = merge_template.format(context=responses).replace("{", "{{").replace("}", "}}")
    final = ask_llm(prompt)
    print(final)
finally:
    driver.quit()
```

---

## 相关笔记

- [[13_Text-to-SQL (SQLlite)]] — Agent + 工具链
- [[05_Output Parsing]] — 结构化输出 / JSON
- [[12_ Agents]] — `create_agent`（本课是链式抽取，非 Agent）
