---
title: Text-to-SQL（Agentic MySQL / SQLite）
aliases:
  - Text-to-SQL
  - SQL Agent
  - 自然语言转 SQL
created: 2026-07-28
updated: 2026-08-01
series: 本地 RAG
part: 13
source: Text to MySQL Agent.ipynb（可删）· 字幕 149–157（可删）
tags:
  - type/literature-note
  - topic/text-to-sql
  - topic/agent
  - topic/sqlite
  - topic/langchain
  - topic/local-rag
  - status/draft
---

# Text-to-SQL（Agentic 查询生成）

> [!summary]
> **本地 RAG · 第 13 部分**。用 `create_agent` + **五件工具**做「自然语言 → SQL」：schema → generate → validate → execute；失败则 **fix**（最多约 3 次）。课名含 MySQL，实现为 **SQLite Employees** + `ChatOllama(qwen3, temperature=0)`。

库：`sqlite:///db/employees_db-full-1.0.6.db`（[fracpete/employees-db-sqlite](https://github.com/fracpete/employees-db-sqlite)）  
入口：`from langchain.agents import create_agent`

## 本章目录

| 章节 | 学什么 |
| --- | --- |
| §1 目标与流程 | 五工具、错误回环 |
| §2 数据与连接 | Employees SQLite、`SQLDatabase` |
| §3 LLM | `temperature=0` |
| §4 五件 `@tool` | schema / generate / validate / execute / fix |
| §5 Agent + `ask_sql` | system prompt、流式演示 |
| 文末实践代码 | 完整可跑骨架 |

---

## 1. 目标与流程

![[13-sql-cell2-0.png]]

| 能力 | 工具 |
| --- | --- |
| 取结构 | `get_database_schema` |
| 生成 SQL | `generate_sql_query`（工具内 LLM） |
| 安全校验 | `validate_sql_query`（仅 SELECT） |
| 执行 | `execute_sql_query` |
| 纠错 | `fix_sql_error`（工具内 LLM） |

```text
用户问题 → sql_agent
  → get_database_schema
  → generate_sql_query
  → validate_sql_query
  → execute_sql_query
       ├─ 成功 → 自然语言答案
       └─ 失败 → fix_sql_error → 再 validate/execute（最多约 3 次）
```

> [!note]
> 标题写 MySQL，URI 与 prompt 规则按 **SQLite**。换方言：改连接串 + generate/fix 里的语法说明即可。Agent **不保证**严格按序（可能跳过 validate），故 `execute` 内会再清洗一遍。

---

## 2. 数据与连接

| 步骤 | 说明 |
| --- | --- |
| 下载 | <https://github.com/fracpete/employees-db-sqlite> |
| 放置 | `db/employees_db-full-1.0.6.db` |
| 表（6） | departments, dept_emp, dept_manager, employees, salaries, titles |

```bash
pip install -U langchain langchain-ollama langchain-community langchain-core python-dotenv
```

```python
import re
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain_core.tools import tool
from langchain.agents import create_agent

load_dotenv()

db = SQLDatabase.from_uri("sqlite:///db/employees_db-full-1.0.6.db")
tables = db.get_usable_table_names()  # 6 张
SCHEMA = db.get_table_info()          # 缓存全库，供工具与 system prompt

# 样例：db.run("select count(*) from employees")  # 约 30 万行量级
```

---

## 3. LLM

```python
llm = ChatOllama(
    model="qwen3",
    base_url="http://localhost:11434",
    temperature=0,  # Text-to-SQL：要事实，不要发散
)
```

---

## 4. 五件工具

### 4.1 `get_database_schema`

```python
@tool
def get_database_schema(table_name: str = None) -> str:
    """Get database schema information for SQL query generation.
    Use this first to understand table structure before creating queries."""
    if table_name:
        tables = db.get_usable_table_names()
        if table_name.lower() in [t.lower() for t in tables]:
            return db.get_table_info([table_name])
        return f"Error: Table '{table_name}' not found. Available tables: {', '.join(tables)}"
    return SCHEMA
```

不传表名 → 全库 `SCHEMA`；表名错 → 返回可用表列表。

### 4.2 `generate_sql_query`

```python
@tool
def generate_sql_query(question: str, schema_info: str = None) -> str:
    """Generate a SQL SELECT query from a natural language question using database schema.
    Always use this after getting schema information."""
    schema_to_use = schema_info if schema_info else SCHEMA
    prompt = f"""
Based on this database schema:
{schema_to_use}

Generate a SQL query to answer this question: {question}

Rules:
- Use only SELECT statements
- Include only existing columns and tables
- Add appropriate WHERE, GROUP BY, ORDER BY clauses as needed
- Limit results to 10 rows unless specified otherwise
- Use proper SQL syntax for SQLite

Return only the SQL query, nothing else.
"""
    return llm.invoke(prompt).content.strip()
```

例：`what is maximum salary in employees` → `SELECT MAX(salary) FROM salaries;`

### 4.3 `validate_sql_query`

```python
@tool
def validate_sql_query(query: str) -> str:
    """Validate SQL query for safety and syntax before execution.
    Returns 'Valid: <query>' if safe or 'Error: <message>' if unsafe."""
    clean = query.strip()
    clean = re.sub(r"```sql\s*", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"```\s*", "", clean)
    clean = clean.strip().rstrip(";")

    if not clean.lower().startswith("select"):
        return "Error: Only SELECT statements are allowed"

    for kw in ["INSERT", "UPDATE", "DELETE", "ALTER", "DROP", "CREATE", "TRUNCATE"]:
        if kw in clean.upper():
            return f"Error: {kw} operations are not allowed"

    return f"Valid: {clean}"
```

### 4.4 `execute_sql_query`

```python
@tool
def execute_sql_query(query: str) -> str:
    """Execute a validated SQL query and return results.
    Only use this after validating the query for safety."""
    clean = query.strip()
    if clean.startswith("Valid: "):
        clean = clean[7:]
    clean = re.sub(r"```sql\s*", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"```\s*", "", clean).strip().rstrip(";")
    try:
        result = db.run(clean)
        return f"Query Results:\n{result}" if result else "Query executed successfully but returned no results."
    except Exception as e:
        return f"Execution Error: {str(e)}"
```

### 4.5 `fix_sql_error`

```python
@tool
def fix_sql_error(original_query: str, error_message: str, question: str) -> str:
    """Fix a failed SQL query by analyzing the error and generating a corrected version.
    Use this when validation or execution fails."""
    fix_prompt = f"""
The following SQL query failed:
Query: {original_query}
Error: {error_message}
Original Question: {question}

Database Schema:
{SCHEMA}

Analyze the error and provide a corrected SQL query that:
1. Fixes the specific error mentioned
2. Still answers the original question
3. Uses only valid table and column names from the schema
4. Follows SQLite syntax rules

Return only the corrected SQL query, nothing else.
"""
    return llm.invoke(fix_prompt).content.strip()
```

---

## 5. Agent 组装与演示

```python
SQL_SYSTEM_PROMPT = f"""You are an expert SQL analyst working with an employees database.

Database Schema:
{SCHEMA}

Your workflow for answering questions:
1. Use `get_database_schema` first to understand available tables and columns (if needed)
2. Use `generate_sql_query` to create SQL based on the question
3. Use `validate_sql_query` to check the query for safety and syntax
4. Use `execute_sql_query` to run the validated query
5. If there's an error, use `fix_sql_error` to correct it and try again (up to 3 times)
6. Provide a clear answer based on the query results

Rules:
- Always follow the workflow step by step
- If a query fails, use the fix tool and try again
- Be precise with table and column names
- If you fail after 3 attempts, explain what went wrong

Remember: Always validate queries before executing them for safety.
"""

tools = [
    get_database_schema,
    generate_sql_query,
    validate_sql_query,
    execute_sql_query,
    fix_sql_error,
]

sql_agent = create_agent(llm, tools, system_prompt=SQL_SYSTEM_PROMPT)


def ask_sql(question: str):
    print(f"\n{'='*60}\nSQL AGENT - Question: {question}\n{'='*60}")
    for event in sql_agent.stream({"messages": question}, stream_mode="values"):
        msg = event["messages"][-1]
        if getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                print(f"\nTool: {tc['name']}\nArgs: {str(tc['args'])[:200]}")
        elif getattr(msg, "content", None):
            print(f"\nAnswer:\n{msg.content}")


ask_sql("What is the average salary of employees in the Sales department?")
# 典型：取 schema → 生成 JOIN →（可能报错）→ fix → 给出平均薪资与可核对 SQL
```

System prompt **内嵌全库 SCHEMA**，并写死工作流与「执行前必须 validate」。

---

## 文末实践代码（精简一体）

把库文件放到 `db/` 后，按 §2–§5 顺序定义 `db`、`SCHEMA`、`llm`、五工具、`SQL_SYSTEM_PROMPT`、`sql_agent`、`ask_sql`，再调用：

```python
ask_sql("What is the average salary of employees in the Sales department?")
ask_sql("what is maximum salary in employees")
```

单测工具可先：

```python
get_database_schema.invoke({"table_name": "departments"})
generate_sql_query.invoke({"question": "what is maximum salary in employees"})
validate_sql_query.invoke({"query": "SELECT MAX(salary) FROM salaries;"})
execute_sql_query.invoke({"query": "SELECT MAX(salary) FROM salaries;"})
```
