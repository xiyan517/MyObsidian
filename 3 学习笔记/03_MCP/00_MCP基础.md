---
title: MCP 基础
aliases:
  - Model Context Protocol
  - 模型上下文协议
  - MCP 入门
  - 00 MCP基础
created: 2026-08-09
updated: 2026-08-09
series: MCP
part: 0
source: Model Context Protocol (MCP) for Beginners 2025-26 · [Build an MCP server · Python](https://modelcontextprotocol.io/docs/2026-07-28/develop/build-server#python)
tags:
  - type/literature-note
  - topic/mcp
  - topic/uv
  - status/draft
---

# MCP 基础

> [!summary]
> 目前只记 **开发环境搭建**：用官方文档在 Windows 上装 `uv`，初始化 `weather` 项目，创建虚拟环境并安装 `mcp[cli]`。后续构建 Server、接 Claude Desktop 等内容再追加。

文档：[Build an MCP server · Python](https://modelcontextprotocol.io/docs/2026-07-28/develop/build-server#python)

相关：[[01_连接生命周期]]

---

## 1. 搭建开发环境（Windows + Python）

### 1.1 环境要求

- Python **3.10+**
- Python MCP SDK **2.0.0+**

### 1.2 安装 `uv`（Windows）

到 [modelcontextprotocol.io](https://modelcontextprotocol.io/) 选 Python → Windows，复制安装命令：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

装完后**重启终端**，确保 `uv` 在 PATH 里。

### 1.3 初始化项目

```powershell
uv init weather
cd weather

uv venv
.venv\Scripts\activate

uv add mcp[cli]

new-item weather.py
```

| 步骤 | 命令 | 作用 |
| --- | --- | --- |
| 建项目 | `uv init weather` | 创建项目目录 |
| 进目录 | `cd weather` | 进入项目 |
| 虚拟环境 | `uv venv` | 创建 `.venv` |
| 激活 | `.venv\Scripts\activate` | 激活环境 |
| 装依赖 | `uv add mcp[cli]` | 安装 MCP CLI |
| 建文件 | `new-item weather.py` | 后续写 Server 用 |

macOS / Linux：激活用 `source .venv/bin/activate`，依赖用 `uv add "mcp[cli]"`，完整命令见官方文档。

---

## 待追加

- [ ] 构建天气 MCP Server
- [ ] 接到 Claude Desktop
