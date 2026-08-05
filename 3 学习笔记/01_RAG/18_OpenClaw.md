---
title: OpenClaw + Ollama（本地个人 AI 助手）
aliases:
  - OpenClaw
  - Clawdbot
  - Ollama OpenClaw
  - OpenClaw Gateway
created: 2026-08-05
updated: 2026-08-05
series: 本地 RAG
part: 18
source: Ollama + OpenClaw 安装演示视频 · https://docs.ollama.com/integrations/openclaw
tags:
  - type/literature-note
  - topic/openclaw
  - topic/ollama
  - topic/local-agent
  - topic/qwen
  - status/draft
---

# OpenClaw + Ollama（本地个人 AI 助手）

> [!summary]
> 用 **Ollama** 一条命令拉起 **OpenClaw**（曾用名 Clawdbot）：本机跑模型、Gateway 做桥、Agent 可调工具。不依赖外部付费 API；适合有较强 GPU 的机器。演示模型：`qwen3.5:9b` → 换 `qwen3.5:27b`。

官方文档：[OpenClaw · Ollama Integrations](https://docs.ollama.com/integrations/openclaw)  
前置：[[01_Ollama Setup]] · 环境见 [[16_杂项]]

## 本章目录

| 章节 | 学什么 |
| --- | --- |
| §1 是什么 | OpenClaw / Gateway / 与 Ollama 的关系 |
| §2 前置条件 | Ollama、Node.js、模型与显存 |
| §3 一键安装 | `ollama launch openclaw` 向导流程 |
| §4 验证与工具审批 | TUI / WebUI、GPU、命令弹窗 |
| §5 换模型 | `openclaw.json`、pull、gateway restart |
| §6 常用命令 | 启动 / 配置 / 停止 |
| §7 踩坑与安全 | 权限、WSL、上下文窗口 |

---

## 1. 是什么

**OpenClaw** 是跑在自己设备上的个人 AI 助手：通过 **Gateway** 把本地（或云端）模型接到 Agent，并支持工具调用（读系统信息、执行命令等）。也可再接到 WhatsApp / Telegram / Slack 等消息渠道。

| 组件 | 作用 |
| --- | --- |
| **Ollama** | 本机拉模型、推理（默认 `http://localhost:11434`） |
| **OpenClaw** | Agent + TUI / WebUI；可装 npm 依赖 |
| **Gateway** | 连接 OpenClaw ↔ Ollama（及后续消息渠道） |

> [!note]
> 旧名 **Clawdbot**。`ollama launch clawdbot` 仍是别名。

价值：本地模型 + 工具能力 ≈ 私人助手；演示里强调「无外部 API、几乎零额外费用」（电费 / 硬件除外）。

---

## 2. 前置条件

1. **安装并启动 Ollama**  
   - Windows：官网下 `.exe`  
   - macOS / Linux：页面命令安装；可用 `ollama serve` 启动  
   - 浏览器打开本机 Ollama 页，应显示 *Ollama is running*
2. **Node.js**（未装时，向导可能提示安装；OpenClaw 经 npm 安装）
3. **先拉好要用的本地模型**（也可在向导里选「下载」）

```bash
# 演示用 9B；显存够可直接上更大档
ollama pull qwen3.5:9b
```

> [!tip]
> 官方建议本地模型 **上下文至少约 64k tokens**。显存不够时先用小模型（如 9B），确认链路通再换大模型。

推荐档位（官方文档，随版本可能变）：

| 类型 | 示例 |
| --- | --- |
| 本地 | `qwen3.5`、`gemma4` |
| 云（Ollama Cloud） | `qwen3.5:cloud`、`kimi-k2.5:cloud` 等 |

---

## 3. 一键安装（课程主路径）

文档页：[docs.ollama.com/integrations/openclaw](https://docs.ollama.com/integrations/openclaw)

在 **PowerShell / 终端** 执行：

```bash
ollama launch openclaw
```

向导大致顺序（与视频一致）：

1. **检测 OpenClaw**：未安装 → 确认后经 npm 安装  
2. **检测 Node.js**：缺则提示安装  
3. **选模型**：例如 Qwen3.5（演示选 9B）  
4. **是否下载模型**：本地已 `pull` 则可直接用  
5. **安全说明**：工具可访问本机；仔细阅读后按需授权  
6. **Onboarding**：配置 provider、安装 Gateway daemon、设 primary model；经 Ollama 启动时通常会启用联网搜索相关插件  
7. **Gateway 启动** → 打开 **TUI**；也可使用带 token 的 **WebUI** 链接

指定模型跳过交互（可选）：

```bash
ollama launch openclaw --model qwen3.5:9b
# 无交互 / CI：
ollama launch openclaw --model qwen3.5:9b --yes
```

只改配置、不立刻起 TUI：

```bash
ollama launch openclaw --config
```

> [!note]
> 官方博客曾写 Windows 更推荐 **WSL**；演示里直接装在 **Windows** 也可跑通。WSL 是可选优化，不是硬门槛。

---

## 4. 验证与工具审批

### 4.1 连通性

- TUI / WebUI 出现后发一句 `hi`，应有 Agent 回复  
- 任务管理器 / `nvidia-smi` 等可看到模型加载与 GPU 占用  

### 4.2 WebUI

- Gateway 日志 / 输出里会有 WebUI URL  
- **URL 末尾 token 必须保留**，否则打不开或无权限  

### 4.3 命令执行弹窗（安全加固）

自 **2026-03-31** 左右更新后，工具执行本机命令常会弹出确认窗（以前多在后台静默执行）。

- 演示建议：**只允许一次（Allow once）**，按需授权  
- 例：问「show me my system configuration」→ Agent 调工具收集软硬件信息 → 弹窗批准 → 汇总回答  

界面「闪烁 / 仍在工作」时表示还在跑工具，等审批与结果即可。

---

## 5. 更换 primary 模型

演示路径：从 **Qwen3.5 9B** 换成更大档（如 **27B**）。

1. 打开 OpenClaw **安装目录**（仓库 / 配置所在处），用 VS Code 打开  
2. 编辑配置（视频中为 `openclaw.json`）：找到 **primary model**，改成目标模型 id  
3. 本机拉取：

```bash
ollama pull qwen3.5:27b   # 以实际模型名为准
```

4. **重启 Gateway**，使新 primary 生效：

```bash
openclaw gateway restart
# 或先 stop 再 launch
openclaw gateway stop
ollama launch openclaw
```

5. 重新打开 WebUI（带 token），确认当前模型已是新档；再发 `hi`，并观察 GPU / 显存占用（大模型会明显更高）

也可用官方推荐方式改模型（不必手改 json）：

```bash
ollama launch openclaw --model qwen3.5:27b
# 或
ollama launch openclaw --config
```

若 Gateway 已在跑，换模型后通常会自动重启以加载新配置。

---

## 6. 常用命令速查

```bash
# 安装 / 启动（推荐入口）
ollama launch openclaw
ollama launch openclaw --model <name>
ollama launch openclaw --config
ollama launch openclaw --model <name> --yes

# Gateway
openclaw gateway start
openclaw gateway restart
openclaw gateway stop
openclaw gateway logs          # 排障时看日志

# 可选：消息渠道 / Web
openclaw configure --section channels
openclaw configure --section web

# 本地模型
ollama pull <model>
ollama serve                  # macOS/Linux 手动起服务时
```

| 概念 | 一句话 |
| --- | --- |
| primary model | Agent 默认用的模型 |
| Gateway | OpenClaw 与 Ollama（及渠道）之间的桥 |
| 工具审批 | 执行本机命令前的显式确认 |

---

## 7. 踩坑与安全

| 点 | 说明 |
| --- | --- |
| 权限 | OpenClaw 可申请较广的本机访问；先读安全说明，再决定「始终允许 / 仅一次 / 拒绝」 |
| 弹窗变多 | 2026-03-31 后更安全，也更啰嗦——正常现象 |
| 多终端 | 启动时打开多个终端窗口，演示认为正常 |
| 显存 | 9B → 27B 显存跳变大；不够就降量化或换小模型 |
| 上下文 | 本地 Agent 建议较大 context（官方约 ≥64k） |
| 联网搜索 | 本地模型走 Ollama web search 时可能需要 `ollama signin` |
| 成本 | 纯本地推理 ≈ 免费 API；云模型则按 Ollama Cloud 计费 |

---

## 相关笔记

- [[01_Ollama Setup]] — Ollama 安装与 CLI  
- [[16_杂项]] — Conda / 环境杂项  
- [[11_Tool Calling]] — 工具调用概念对照  
- [[12_ Agents]] — Agent 思路对照  
- [[17_BlearnMCP]] — 另一类「本地工具 + 模型」链路（Blender MCP）

## 待处理

- [ ] 本机确认 `openclaw.json` 实际路径与字段名（随版本可能变）  
- [ ] 是否接入 Telegram / WhatsApp 等渠道（`openclaw configure --section channels`）  
- [ ] 需要时补充一份「仅 WSL 安装」对照步骤
