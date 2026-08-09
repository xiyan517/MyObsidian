---
title: MCP 基础
aliases:
  - MCP 环境搭建
  - 构建MCPServer
  - 天气 MCP
  - weather MCP
created: 2026-08-09
updated: 2026-08-09
tags:
  - type/literature-note
  - topic/mcp
  - topic/python
  - topic/uv
  - status/draft
---

# MCP 基础

文档：[Build an MCP server · Python](https://modelcontextprotocol.io/docs/2026-07-28/develop/build-server#python)

要求：Python 3.10+，MCP SDK 2.0.0+

> [!summary]
> 三块：① 用 `uv` 搭环境；② 对接 NWS 构建天气 MCP Server（`get_alerts` / `get_forecast`，stdio）；③ 写进 Claude Desktop 配置并实测调用。

## 本章目录

| 章节 | 做什么 |
| --- | --- |
| **一、环境搭建** | |
| §1 安装 uv | Windows 装包管理器 |
| §2 初始化项目 | 虚拟环境 + 依赖 + 源文件 |
| **二、构建 MCP Server** | |
| §3 依赖与客户端 | `MCPServer` + NWS 请求封装 |
| §4 格式化警报 | GeoJSON feature → 可读文本 |
| §5 Tool：州级警报 | `get_alerts(state)` |
| §6 Tool：经纬度预报 | `get_forecast(lat, lon)` |
| §7 入口与运行 | `mcp.run(transport="stdio")` |
| **三、配置 MCP 使用** | |
| §8 Claude Desktop | `claude_desktop_config.json` |
| §9 验证与试问 | 重启、工具列表、示例提问 |
| §10 排错 | 路径、`uv`、完全退出 |

---

# 一、环境搭建

## 1. 安装 uv（Windows）

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

装完重启终端。

> [!warning]
> 不重启终端的话，常会提示找不到 `uv`（PATH 还没生效）。

## 2. 初始化项目

```powershell
uv init weather
cd weather

uv venv  # 使用 conda 环境的话：若后续还需复用这个环境则执行；否则可跳过创建虚拟环境
.venv\Scripts\activate

uv add "mcp[cli]"
uv add httpx

new-item weather.py
```

| 命令 | 作用 |
| --- | --- |
| `uv init weather` | 建项目 |
| `uv venv` | 建虚拟环境 |
| `.venv\Scripts\activate` | 激活环境 |
| `uv add "mcp[cli]"` | 装 MCP |
| `uv add httpx` | 装 HTTP 客户端（调 NWS API） |
| `new-item weather.py` | 建 Server 文件 |

> [!note]
> macOS / Linux：激活用 `source .venv/bin/activate`，装包用 `uv add "mcp[cli]"`（带引号，避免 shell 解析 `[]`）。

> [!warning]
> 先 `activate` 再装依赖。没进虚拟环境时，包可能装到系统 Python 里。

---

# 二、构建 MCP Server

对接 [api.weather.gov](https://api.weather.gov)：HTTP 拉数据 → 两个 `@mcp.tool()` → `stdio` 跑起来。把下面代码写入 `weather.py`。

> [!note]
> 官方教程里常见写法是 `from mcp.server.fastmcp import FastMCP`。下面用当前 SDK 的 `MCPServer`；若导入失败，可改回 FastMCP。

## 3. 依赖与客户端

```python
from typing import Any
import httpx
from mcp.server import MCPServer

# from mcp.server.fastmcp import FastMCP

mcp = MCPServer("weather")

USER_AGENT = "weather-app/1.0"
NWS_API_BASE = "https://api.weather.gov"


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None
```

## 4. 格式化警报

```python
def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get("event", "Unknown")}
Area: {props.get("areaDesc", "Unknown")}
Severity: {props.get("severity", "Unknown")}
Description: {props.get("description", "No description available")}
Instructions: {props.get("instruction", "No specific instructions provided")}
"""
```

## 5. Tool：州级天气警报

```python
@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)
```

## 6. Tool：经纬度预报

两步：先 `/points/{lat},{lon}` 拿 forecast URL，再拉详细时段（只展示前 5 段）。

```python
@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period["name"]}:
Temperature: {period["temperature"]}°{period["temperatureUnit"]}
Wind: {period["windSpeed"]} {period["windDirection"]}
Forecast: {period["detailedForecast"]}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)
```

## 7. 入口与运行

```python
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

```powershell
uv run weather.py
```

> [!warning]
> NWS 要求自定义 `User-Agent`；没有的话请求常被拒。本例用 `weather-app/1.0`。

---

# 三、配置 MCP 使用

把本地 `weather` Server 注册到 **Claude Desktop**：客户端按配置用 stdio 拉起 `uv run weather.py`，对话里就能调两个 tool。

> [!note]
> Claude Desktop 在 Linux 上尚不可用时，可改走[自建 MCP Client](https://modelcontextprotocol.io/docs/develop/build-client)，或在 Cursor 等支持 MCP 的客户端里用同类 `command` / `args` 配置。

## 8. 配置 Claude Desktop

### 8.1 打开配置文件

| 系统 | 路径 |
| --- | --- |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |

PowerShell 一键打开（没有文件就先建）：

```powershell
code $env:AppData\Claude\claude_desktop_config.json
```

### 8.2 注册 weather 服务器

`--directory` 必须是项目**绝对路径**（改成你本机 `weather` 目录）。Windows 路径用 `\\` 或 `/`。

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\ABSOLUTE\\PATH\\TO\\PARENT\\FOLDER\\weather",
        "run",
        "weather.py"
      ]
    }
  }
}
```

| 字段               | 含义                                                        |
| ---------------- | --------------------------------------------------------- |
| `mcpServers`     | 所有本地 MCP Server 的注册表；Claude 启动时按这里的条目拉起进程                 |
| `"weather"`      | Server 在客户端里的**名字**（可自定）；对话里工具会挂在这个名字下                    |
| `command`        | 要执行的可执行文件；这里用 `uv` 来跑项目（找不到时改成 `uv` 的绝对路径）                |
| `args`           | 传给 `command` 的参数列表，按顺序拼接                                  |
| `--directory`    | 后一项是工作目录：进到该目录再执行后续命令（保证能读到项目依赖 / `pyproject.toml`）       |
| `C:\\…\\weather` | 项目根目录的**绝对路径**（占位符，须改成本机路径）；Windows 用 `\\` 或 `/`          |
| `run`            | `uv run`：用当前项目环境执行脚本（自动带上已装的 `mcp` / `httpx`）             |
| `weather.py`     | 入口脚本；里面的 `mcp.run(transport="stdio")` 与 Claude 通过标准输入输出通信 |

拼起来等价于：

```text
uv --directory <项目绝对路径> run weather.py
```

macOS / Linux：

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/PARENT/FOLDER/weather",
        "run",
        "weather.py"
      ]
    }
  }
}
```

> [!warning]
> 若 Claude 找不到 `uv`，把 `command` 改成 `uv` 的完整路径。查路径：PowerShell 用 `where.exe uv`，macOS / Linux 用 `which uv`。

已有其他 Server（如 [[17_BlenderMCP]] 的 `blender`）时，只在 `mcpServers` 里**追加** `weather` 键，不要整文件覆盖。

## 9. 验证与试问

1. **保存** `claude_desktop_config.json`
2. **完全退出**再打开 Claude Desktop（托盘图标也要 Quit，不是只关窗口）
3. **新开一条对话**（旧会话可能不刷新工具列表）
4. 界面应出现 MCP / 锤子类工具入口；里面有 `get_alerts`、`get_forecast`

可试：

- What's the weather in Sacramento?
- What are the active weather alerts in Texas?
- 用经纬度查旧金山预报（约 `37.77, -122.42`）

Claude 调用 tool 前可能弹出**批准**，允许后才会真正请求 NWS。

## 10. 排错

| 现象 | 处理 |
| --- | --- |
| 看不到 MCP / weather | 检查 JSON 语法；路径是否绝对；完全退出再开；新开对话 |
| Server disconnected | `command` 是否指向可用的 `uv`；`--directory` 是否指到含 `weather.py` 的目录 |
| 工具在但不返回数据 | 本机能否访问 `api.weather.gov`；`User-Agent` 是否已写 |

查日志（可选）：

| 系统 | 日志位置 |
| --- | --- |
| Windows | `%APPDATA%\Claude\logs` |
| macOS | `~/Library/Logs/Claude` |

## 相关笔记

- [[17_BlenderMCP]]（同类：写 `claude_desktop_config.json`）
- [[18_OpenClaw]]
