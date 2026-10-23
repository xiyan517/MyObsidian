# -*- coding: utf-8 -*-
import pathlib

p = next(pathlib.Path(r"d:/MyObsidian").glob("3 */11_Agent/02_Agentic.md"))
t = p.read_text(encoding="utf-8")

t = t.replace(
    "来源：吴恩达 《Agentic AI》· P03–P18",
    "来源：吴恩达 《Agentic AI》· P03–P19",
    1,
)

old_sum = (
    "> **agentic** 是程度不是开关。落地先 SOP+文本。关键：**拆步**、**Evals**、四大模式。"
    "M2 Reflection。M3 **Tool Use**（含代码执行沙箱）+ **MCP**（M+N 替代 M×N）。"
    "下一模块：**Evals / 错误分析**（吴恩达称或为本课最重要模块）。"
)
new_sum = (
    "> **agentic** 是程度不是开关。落地先 SOP+文本。关键：**拆步**、**Evals**、四大模式。"
    "M2 Reflection · M3 Tool Use/MCP。"
    "M4：**先糙快原型 → 读输出找坑 → 小 eval 驱动改进**；端到端 eval 二维：客观/主观 × 有无逐例 GT。"
)
if old_sum not in t:
    raise SystemExit("top summary not found")
t = t.replace(old_sum, new_sum, 1)

# Cross-ref §8
old_8 = "能否高效做出好用的 agentic workflow，很大程度取决于有没有 **纪律性的评估（evals）**。本节约览；课程 Module 4 会深挖。"
new_8 = "能否高效做出好用的 agentic workflow，很大程度取决于有没有 **纪律性的评估（evals）**。本节约览；展开见 **Module 4 §27+**（P19）。"
if old_8 not in t:
    raise SystemExit("§8 intro not found")
t = t.replace(old_8, new_8, 1)

marker = "    下一模块\n      Evals · 错误分析\n```"
idx = t.find(marker)
if idx < 0:
    raise SystemExit("M3 takeaway end not found")
end = idx + len(marker)

new_m4 = """    下一模块
      Evals · 错误分析
```

---

# Module 4：构建 Agentic AI 的实用技巧

来源：P19 · 评估（evals）

> [!summary]
> 事先很难知道系统哪里会挂 → **先负责任地做出糙快原型**，读输出定优先级。  
> 发现痛点后：会修就修；要长期改 → 建 **小 eval（常 10–20 例）** 跟踪。  
> 端到端 eval 可沿两轴想：**代码 vs LLM-as-Judge** × **有无逐例 ground truth**。

> [!tip] 读图颜色
> 🔴 用户输入　⚪ LLM　🟢 工具/代码评测

---

## 27. 评估（Evals）（P19）

### 27.1 心态：先建、再盯、再聚焦

开发 agentic 时，很难提前知道哪里好、哪里差、该把力气花在哪。

| 少做 | 多做 |
| --- | --- |
| 空坐几周只空想架构 | **安全、不泄密** 前提下尽快做出可看的原型 |
| 指望一次设计完美 eval | 先看输出 → 再决定 **评什么** |

```mermaid
flowchart LR
  Proto[糙快原型] --> Read[读 10–20 条输出]
  Read --> Spot[发现常见错误模式]
  Spot --> Eval[建小 eval 跟踪]
  Eval --> Improve[改 prompt / 算法]
  Improve --> Read
```

### 27.2 例① 发票：到期日抽错

任务：抽四个字段写库。通读约 20 张发票 → 常把 **开票日** 和 **到期日** 搞混（业务要的是到期日，好按时付）。

→ 结论：常见失败模式在日期 → 既要改抽取，也宜建 **到期日准确率** eval。  
（若实际是开票方地址常错——尤其国际非英文名——则应把 eval 重心放在地址，而非日期。）

**建评测集（示意）：**

1. 找 10–20 张发票，手写正确到期日（如 `2025-08-20`）  
2. Prompt 要求模型 **始终** 用年-月-日格式输出到期日  
3. 代码用正则抽出该日期，与 GT 比对是否相等  
4. 改系统时盯 **正确率是否上升**

> [!important]
> 循环：**看输出找不满意处 → 会修就修；要长期打磨 → 上小 eval 驱动**。评测集不够覆盖时可 **随时加例**，让它更贴近你对「够不够好」的判断。

### 27.3 例② 营销文案：字数超限

需求：Instagram 配文 **最多 10 词**（墨镜图 +「写卖点文案」等）。  
读输出：语气尚可，但常超长（17 / 14 / 11 词…）→ 痛点是 **长度**。

| 步骤 | 做法 |
| --- | --- |
| 测试集 | 约 10–20 个商品图/查询 |
| 度量 | 代码算 word count，与上限 10 比 |
| 与发票例的差别 | **无逐例 GT**——每条目标都是同一个「≤10」 |

复杂生成工作流同样可用这类 eval。

### 27.4 例③ 研究 Agent：漏掉关键点

读多篇输出：黑洞进展漏掉高曝光结果；西雅图租 vs 买尚可；采果机器人没提头部设备商……  
→ 常 **漏掉人类专家会写的要点**。

建 eval：

1. 若干主题 prompt；每个准备 **3–5 条 gold talking points**（**有逐例标注**，主题不同点不同）  
2. **LLM-as-Judge**：数文中覆盖了几条要点（表述方式太多，正则难搞）  
3. 返回如 JSON：`score`（0–5）+ `explanation`

→ 偏主观的「是否充分提到事件视界」等，用 Judge 更合适。

### 27.5 二维：四种端到端 Eval

本讲这些都是 **端到端（end-to-end）**：一端用户输入，一端最终输出。

|  | **有逐例 Ground Truth** | **无逐例 GT**（全局同一标准） |
| --- | --- | --- |
| **客观：写代码评** | 发票到期日 vs 手标日期 | 文案 word count ≤ 10 |
| **主观：LLM-as-Judge** | 金标要点覆盖数 | 图表按同一 **rubric** 打分（咖啡机销量图课例） |

```mermaid
flowchart TB
  subgraph 客观·代码
    A[有GT：发票到期日]
    B[无GT：文案字数≤10]
  end
  subgraph 主观·Judge
    C[有GT：金标要点覆盖]
    D[无GT：图表同一rubric]
  end
  style A fill:#bbf7d0
  style B fill:#d9f99d
  style C fill:#fef08a
  style D fill:#fed7aa
```

### 27.6 设计端到端 Eval 的技巧

| 技巧 | 说明 |
| --- | --- |
| **糙快起步** | 别被「要花好几周建完美 eval」吓瘫；10–15–20 例 + 代码或 Judge 即可开跑 |
| **Eval 也要迭代** | 像改 workflow 一样持续改评测 |
| **人眼 + 指标** | 初期两者并用；评测变成熟后，可更多信指标，少每次改 prompt 就通读几百条 |
| **指标与直觉不符时** | 你觉得新系统明显更好但分数没涨 → 往往该 **加大/改评测**，让它对齐你的判断 |
| **找灵感** | 许多任务是在自动化「人能做的事」→ 盯 **明显不如熟练人类** 的地方，决定下一步改什么 |

下一讲：如何用 evals **定位整条链里最值得改的组件**（agentic 多环节时的关键效率技能）。

---

## 28. 带走（Module 4 · 本讲）

```mermaid
mindmap
  root((Evals P19))
    流程
      原型→读输出→小eval→改进
    三例
      发票·代码+GT
      文案·代码·无逐例GT
      研究·Judge+金标点
    两轴
      客观/主观
      有无逐例GT
    技巧
      糙快起步
      迭代eval
      对齐人类判断
    下一讲
      组件级聚焦
```
"""

p.write_text(t[:idx] + new_m4, encoding="utf-8")
print("ok", p)
