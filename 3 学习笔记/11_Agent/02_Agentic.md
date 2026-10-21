---
title: Agentic — 自主性、优势与应用
aliases:
  - agentic
  - 自主性谱系
  - degrees of autonomy
  - agentic workflow 优势
  - agentic 应用
  - computer use
  - 吴恩达 Agentic AI
created: 2026-10-21
updated: 2026-10-21
tags:
  - type/literature-note
  - topic/agent
  - topic/agentic
  - source/andrew-ng
  - status/draft
---

# Agentic：自主性、优势与应用

> [!summary]
> **agentic** 描述程度，不争论「算不算 Agent」。自主性：低 → 半 → 高。三大优势：效果、并行、模块化。落地从 **有 SOP、偏文本** 起步；步骤未知 / Computer Use 更难。核心技能：**任务拆步**。

来源：吴恩达 《Agentic AI》· P03–P05

> [!tip] 读图颜色（课内约定）
> 🔴 用户输入　⚪ LLM　🟢 工具/其它软件

---

## 1. 用 agentic，少争定义

```mermaid
flowchart LR
  subgraph 旧习惯
    A[是 Agent?] -->|是| B[算]
    A -->|否| C[不算]
  end
  subgraph 更好
    D[agentic 程度] --> E[低]
    D --> F[半]
    D --> G[高]
  end
  旧习惯 -.->|换成| 更好
```

| 旧习惯 | 问题 | 更好做法 |
| --- | --- | --- |
| 二元：是 / 不是 Agent | 定义战 | 用 **agentic** 作形容词 |
| 争论「够不够自主」 | 耽误构建 | 承认程度不同，继续做 |

**自主性是连续谱，不是开关。**

---

## 2. 同一任务：低自主 vs 高自主

任务：写一篇关于黑洞的文章。**核心差别：谁决定下一步。**

### 低自主：工程师写死流水线

```mermaid
flowchart LR
  U([用户请求]) --> L1[LLM<br/>生成检索词]
  L1 --> T1[网页搜索]
  T1 --> T2[抓取网页]
  T2 --> L2[LLM<br/>写文章]
  L2 --> O([成稿])

  classDef user fill:#fecaca,stroke:#b91c1c
  classDef llm fill:#e5e7eb,stroke:#6b7280
  classDef tool fill:#bbf7d0,stroke:#15803d
  class U,O user
  class L1,L2 llm
  class T1,T2 tool
```

- 步骤 **确定性**（programmer 定死）
- 工具调用 **硬编码**
- LLM 主要负责 **生成文本**

### 高自主：LLM 当调度员

```mermaid
flowchart TB
  U([用户请求]) --> L1{LLM 决定<br/>搜哪里？}
  L1 -->|网页| T1[网页搜索]
  L1 -->|新闻| T2[新闻搜索]
  L1 -->|论文| T3[arXiv]
  T1 & T2 & T3 --> L2{抓几页？<br/>PDF 要转文本？}
  L2 --> T4[抓取 / PDF→文本]
  T4 --> L3[写草稿]
  L3 --> L4{够好？}
  L4 -->|再抓| L2
  L4 -->|完成| O([成稿])

  classDef user fill:#fecaca,stroke:#b91c1c
  classDef llm fill:#e5e7eb,stroke:#6b7280
  classDef tool fill:#bbf7d0,stroke:#15803d
  class U,O user
  class L1,L2,L3,L4 llm
  class T1,T2,T3,T4 tool
```

- 执行顺序可由 **LLM 决定**
- 工具选择、次数、是否回环都更动态

---

## 3. 自主性谱系

```mermaid
flowchart LR
  L[低自主<br/>步骤写死<br/>工具硬编码] --> M[半自主<br/>工具预置<br/>LLM 选用]
  M --> H[高自主<br/>LLM 定流程<br/>甚至造工具]

  style L fill:#dbeafe,stroke:#1d4ed8
  style M fill:#fef3c7,stroke:#b45309
  style H fill:#fee2e2,stroke:#b91c1c
```

| 档位 | 谁定步骤 | 工具 | LLM 干什么 |
| --- | --- | --- | --- |
| **低** | 工程师预先定死 | 调用常硬编码 | 主要生成文本 |
| **半** | 部分决策交给 LLM | 工具预定义，LLM **选用** | 选工具、部分规划 |
| **高** | LLM 自定步骤序列 | 甚至可 **写新函数 / 造工具** | 规划 + 选工具 + 可能造工具 |

```text
要稳定、可预期  ←——————→  开放探索、可接受不可控
        偏左（企业大量落地）          偏右（更前沿）
```

> [!important]
> **不是越自主越好。** 先按可控性需求选位置。

---

## 4. 三大优势

最大卖点：许多 **以前做不好** 的任务变得可行。

### 4.1 效果：换工作流 > 换模型

HumanEval（写代码）课例示意（后两档为定性，非精确数字）：

```mermaid
flowchart TB
  A["3.5 一次生成 · ~40%"] -->|换代| B["4 一次生成 · ~67%"]
  A -->|加 agentic<br/>提升往往更大| C["3.5 + agentic · 更高"]
  B -->|加 agentic| D["4 + agentic · 再上"]
  style A fill:#e5e7eb
  style B fill:#93c5fd
  style C fill:#86efac
  style D fill:#4ade80
```

模型换代（3.5→4）已经很大，但把 **上一代** 包进 agentic，提升往往 **更大**。

→ **先设计工作流，别只等更强模型。**

### 4.2 并行：相对人类更快

```mermaid
flowchart TB
  subgraph 人类
    H1[页1] --> H2[页2] --> H3[页3] --> H9[…页9]
  end
  subgraph Agentic
    direction LR
    A1[页1] --- A2[页2] --- A3[页3] --- A9[…页9]
  end
  Agentic --> W[汇总 → LLM 写文]
```

| 对比 | 结论 |
| --- | --- |
| vs 单次 prompt | Agentic **更慢**（多轮多步） |
| vs 人类串行研究 | 可并行抓取，**往往更快** |

### 4.3 模块化：拼最佳组件

```mermaid
flowchart LR
  U([请求]) --> L1[LLM A]
  L1 --> S{搜索组件}
  S -->|可换| G[Google]
  S -->|可换| B[Bing / DDG]
  S -->|可换| T[Tavily / You]
  S -->|可换| N[新闻搜索]
  G & B & T & N --> L2[LLM B<br/>可与 A 不同厂商]
  L2 --> O([输出])

  classDef user fill:#fecaca,stroke:#b91c1c
  classDef llm fill:#e5e7eb,stroke:#6b7280
  classDef tool fill:#bbf7d0,stroke:#15803d
  class U,O user
  class L1,L2 llm
  class G,B,T,N tool
```

习惯：盯 **单个组件** 做增删替换，整条链不要绑死一家。

---

## 5. 应用案例（由易到难）

```mermaid
flowchart LR
  E[发票处理] --> O[订单问询+人审] --> C[通用客服] --> CU[Computer Use]
  style E fill:#bbf7d0,stroke:#15803d
  style O fill:#d9f99d,stroke:#65a30d
  style C fill:#fef08a,stroke:#ca8a04
  style CU fill:#fecaca,stroke:#b91c1c
```

### 5.1 发票处理（易）

目标：开票方、地址、金额、到期日 → 写库按时付。

```mermaid
flowchart LR
  PDF([发票 PDF]) --> T[PDF→文本/MD]
  T --> L1{是发票?}
  L1 -->|否| X[忽略]
  L1 -->|是| L2[抽取字段]
  L2 --> DB[(写数据库)]

  classDef user fill:#fecaca,stroke:#b91c1c
  classDef llm fill:#e5e7eb,stroke:#6b7280
  classDef tool fill:#bbf7d0,stroke:#15803d
  class PDF user
  class L1,L2 llm
  class T,DB tool
```

有明确 SOP → 易做成可靠逐步 workflow。

### 5.2 客户订单问询（稍难 · 人审）

```mermaid
flowchart LR
  M([客户邮件]) --> L1[抽取订单/姓名]
  L1 --> DB[(查订单库)]
  DB --> L2[起草回复]
  L2 --> Q[入人工审核队列]
  Q --> H{人通过?}
  H -->|是| S[发出]
  H -->|否| E[修改/驳回]

  classDef user fill:#fecaca,stroke:#b91c1c
  classDef llm fill:#e5e7eb,stroke:#6b7280
  classDef tool fill:#bbf7d0,stroke:#15803d
  class M user
  class L1,L2 llm
  class DB,Q,S tool
```

步骤仍清晰；许多企业已在部署。

### 5.3 通用客服（更难 · 步骤未知）

```mermaid
flowchart TB
  Q1([有黑/蓝牛仔裤吗？]) --> P1[规划：查黑库存 + 查蓝库存] --> A1[合并作答]
  Q2([退货沙滩巾]) --> P2[核实购买 → 查退货政策 → 出单 + 更新库] --> A2[完成退货流程]
```

步骤 **不能预先写死**，要边走边规划 → 更难控。

### 5.4 Computer Use（很难 · 前沿）

课例：查 United 两班 SFO→DCA 是否有座。

```mermaid
flowchart TB
  U([查航班座位]) --> W1[打开 United 官网]
  W1 --> C{卡住/解析失败?}
  C -->|是| G[改走 Google Flights]
  G --> F[找到匹配航班]
  F --> W2[绕回 United 对应页]
  C -->|否| W2
  W2 --> O([确认：有座])

  classDef user fill:#fecaca,stroke:#b91c1c
  classDef llm fill:#e5e7eb,stroke:#6b7280
  classDef tool fill:#bbf7d0,stroke:#15803d
  class U,O user
  class C llm
  class W1,G,F,W2 tool
```

> [!warning]
> 页面慢加载会懵；很多页尚解析不准 → **暂不宜上关键路径**，但是重要方向。

---

## 6. 什么任务更好做

```mermaid
flowchart TB
  subgraph 更容易
    direction LR
    E1[有 SOP] --- E2[纯文本] --- E3[发票 / 订单邮件]
  end
  subgraph 更难
    direction LR
    H1[步骤未知] --- H2[多模态] --- H3[Computer Use / 开放客服]
  end
  更容易 -->|难度上升| 更难
  style E1 fill:#bbf7d0
  style E2 fill:#bbf7d0
  style E3 fill:#bbf7d0
  style H1 fill:#fecaca
  style H2 fill:#fecaca
  style H3 fill:#fecaca
```

| 更容易 | 更难 |
| --- | --- |
| 已有 SOP，可逐步固化 | 步骤事先未知，边做边规划 |
| **纯文本**（LLM 所长） | 多模态（音/视）——能做但更脆 |
| 发票、订单邮件 | Computer Use、开放域客服 |

落地口诀：复杂流程 → **拆成可逐步执行的步骤** → 再做成 agentic workflow。  
下一讲：**任务分解（task decomposition）**。

---

## 7. 带走

```mermaid
mindmap
  root((Agentic))
    程度不是开关
      低 / 半 / 高
      谁定下一步
    三大优势
      效果常超换代
      并行快于人
      组件可换
    落地
      先 SOP + 文本
      拆步再实现
      Computer Use 往后放
```
