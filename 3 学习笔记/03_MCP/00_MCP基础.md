# MCP 基础

文档：[Build an MCP server · Python](https://modelcontextprotocol.io/docs/2026-07-28/develop/build-server#python)

要求：Python 3.10+，MCP SDK 2.0.0+

> [!note]
> 目前只记开发环境搭建。后面再补：写天气 Server、接到 Claude Desktop。

## 安装 uv（Windows）

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

装完重启终端。

> [!warning]
> 不重启终端的话，常会提示找不到 `uv`（PATH 还没生效）。

## 初始化项目

```powershell
uv init weather
cd weather

uv venv  # 使用conda 环境的化如果后续还需复用这个环境则需要执行 否则跳过创建虚拟环境
.venv\Scripts\activate

uv add mcp[cli]

new-item weather.py
```

| 命令 | 作用 |
| --- | --- |
| `uv init weather` | 建项目 |
| `uv venv` | 建虚拟环境 |
| `.venv\Scripts\activate` | 激活环境 |
| `uv add mcp[cli]` | 装 MCP |
| `new-item weather.py` | 建 Server 文件 |

> [!note]
> macOS / Linux：激活用 `source .venv/bin/activate`，装包用 `uv add "mcp[cli]"`（带引号，避免 shell 解析 `[]`）。

> [!warning]
> 先 `activate` 再装依赖。没进虚拟环境时，包可能装到系统 Python 里。

## 待追加

- [ ] 构建天气 MCP Server
- [ ] 接到 Claude Desktop
