# stock-analyst-cat 架构重构实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将单一技能拆分为3个专业Skill（stock-editor、stock-analyst、stock-reviewer），实现多代理协作

**Architecture:** 采用主编调度+双代理模式，主编负责场景解析/搜索调度/轻审/输出，分析代理负责深度分析，审查代理负责质量审查

**Tech Stack:** OpenClaw Skill系统、Subagent调度、mcporter搜索

---

## Chunk 1: 创建stock-editor主编Skill

**目标:** 创建主编skill的核心骨架，定义基本结构和场景解析功能

### Task 1.1: 创建stock-editor目录结构

**Files:**
- Create: `C:\Users\Administrator\.claude\skills\stock-analyst-cat\stock-editor\SKILL.md`
- Create: `C:\Users\Administrator\.claude\skills\stock-analyst-cat\stock-editor\references\01-scenes.md`
- Create: `C:\Users\Administrator\.claude\skills\stock-analyst-cat\stock-editor\memory\self-improving.md`

- [ ] **Step 1: 创建stock-editor目录**

```
在 stock-analyst-cat/ 下创建：
stock-editor/
├── SKILL.md
├── references/
│   └── 01-scenes.md
└── memory/
    └── self-improving.md
```

- [ ] **Step 2: 编写SKILL.md主入口**

```markdown
---
name: stock-editor
description: 主编Skill，负责场景解析、任务分解、搜索调度、轻审、输出
---

# stock-editor (主编)

## 职责
- 场景理解：解析用户意图
- 任务分解：拆解子任务
- 搜索调度：并行搜索热点
- 轻审：30秒快速检查
- 结果汇总：统一格式
- 最终输出：格式化报告

## 场景类型
- pre_market: 盘前扫描
- intra_day: 盘中分析
- after_market: 收盘复盘
- stock_analysis: 个股分析

## 调用代理
- 分析代理：stock-analyst
- 审查代理：stock-reviewer
```

- [ ] **Step 3: 创建场景定义文档**

```markdown
# 场景定义

## 场景类型

| 场景 | 关键词 | 输出要求 |
|------|--------|----------|
| pre_market | 盘前、开盘前、早上 | 热点预测报告 |
| intra_day | 盘中、上午、下午、现在 | 实时热点分析 |
| after_market | 复盘、收盘、盘后、昨日 | 复盘报告 |
| stock_analysis | 个股、股票代码 | 个股分析报告 |
```

- [ ] **Step 4: Commit**

---

### Task 1.2: 实现场景解析功能

**Files:**
- Modify: `C:\Users\Administrator\.claude\skills\stock-analyst-cat\stock-editor\SKILL.md`

- [ ] **Step 1: 添加场景解析逻辑到SKILL.md**

```markdown
## 场景解析

根据用户输入识别场景类型：

| 用户输入关键词 | 场景 |
|---------------|------|
| 盘前、开盘前、早上、早晨 | pre_market |
| 盘中、上午、下午、现在 | intra_day |
| 复盘、收盘、盘后、昨天、今日 | after_market |
| 个股、股票、600、000、002 | stock_analysis |

**默认场景**: pre_market（盘前扫描）
```

- [ ] **Step 2: Commit**

---

## Chunk 2: 创建stock-analyst分析代理Skill

**目标:** 创建分析代理skill，迁移现有分析逻辑

### Task 2.1: 创建stock-analyst目录结构

**Files:**
- Create: `C:\Users\Administrator\.claude\skills\stock-analyst-cat\stock-analyst\SKILL.md`
- Create: `C:\Users\Administrator\.claude\skills\stock-analyst-cat\stock-analyst\references\01-analysis.md`
- Create: `C:\Users\Administrator\.claude\skills\stock-analyst-cat\stock-analyst\references\02-rating.md`
- Create: `C:\Users\Administrator\.claude\skills\stock-analyst-cat\stock-analyst\memory\self-improving.md`

- [ ] **Step 1: 创建stock-analyst目录**

```
stock-analyst/
├── SKILL.md
├── references/
│   ├── 01-analysis.md
│   └── 02-rating.md
└── memory/
    └── self-improving.md
```

- [ ] **Step 2: 编写SKILL.md主入口**

```markdown
---
name: stock-analyst
description: 分析代理Skill，负责深度分析、逻辑锻造、态势评级、作战地图
---

# stock-analyst (分析代理)

## 职责
- 深度分析：多维度分析热点
- 逻辑锻造：构建因果逻辑链条
- 态势评级：给出评级（核爆/沸腾/发酵/观望）
- 作战地图：核心突击位/侧翼观测位/路标
- 风险评估：识别风险信号

## 输入格式
{
  "scene": "盘前扫描",
  "hotspots": [
    {
      "name": "煤炭板块",
      "score": 85,
      "search_results": [...]
    }
  ],
  "time_window": {...}
}

## 输出格式
{
  "hotspot_name": "煤炭板块",
  "analysis": {
    "situation_rating": "⚡⚡⚡⚡沸腾级",
    "drive_type": "多重驱动",
    "battle_map": {...},
    "risks": [...]
  },
  "quality_score": 85
}
```

- [ ] **Step 3: 创建分析逻辑文档**

```markdown
# 分析逻辑

## 分析维度

1. **消息面驱动**：政策、技术、业绩、事件
2. **市场预期**：资金流向、板块热度、机构预期
3. **情绪驱动**：舆情热度、社交讨论、市场关注

## 态势评级标准

| 评级 | 阈值 | 符号 |
|------|------|------|
| 核爆级 | ≥90分 | ⚡⚡⚡⚡⚡ |
| 沸腾级 | ≥75分 | ⚡⚡⚡⚡ |
| 发酵级 | ≥50分 | ⚡⚡⚡ |
| 观望级 | ≥40分 | ⚡⚡ |
```

- [ ] **Step 4: Commit**

---

## Chunk 3: 创建stock-reviewer审查代理Skill

**目标:** 创建审查代理skill，定义质量检查标准

### Task 3.1: 创建stock-reviewer目录结构

**Files:**
- Create: `C:\Users\Administrator\.claude\skills\stock-analyst-cat\stock-reviewer\SKILL.md`
- Create: `C:\Users\Administrator\.claude\skills\stock-analyst-cat\stock-reviewer\references\01-quality.md`
- Create: `C:\Users\Administrator\.claude\skills\stock-analyst-cat\stock-reviewer\references\02-checklist.md`
- Create: `C:\Users\Administrator\.claude\skills\stock-analyst-cat\stock-reviewer\memory\self-improving.md`

- [ ] **Step 1: 创建stock-reviewer目录**

```
stock-reviewer/
├── SKILL.md
├── references/
│   ├── 01-quality.md
│   └── 02-checklist.md
└── memory/
    └── self-improving.md
```

- [ ] **Step 2: 编写SKILL.md主入口**

```markdown
---
name: stock-reviewer
description: 审查代理Skill，负责质量审查、信源核查、逻辑校验
---

# stock-reviewer (审查代理)

## 职责
- 质量审查：深度检查分析报告
- 信源核查：验证S1/S2/A/B级信源
- 逻辑校验：检查逻辑链条
- 风险复核：确认风险预警
- 修改建议：给出具体修改建议

## 严审检查清单

1. 态势评级是否符合标准？
2. 信源是否S1/S2/A级为主？
3. 作战地图四要素是否完整？
4. 风险预警是否包含具体阈值？
5. 利好类型是否标注？
6. 关键路标是否可验证？
7. 是否有遗漏的≥75分热点？

## 审查反馈格式

{
  "passed": true/false,
  "quality_score": 60-100,
  "issues": [
    {
      "type": "致命/建议",
      "severity": "high/medium/low",
      "location": "位置",
      "problem": "问题",
      "suggestion": "建议"
    }
  ],
  "summary": "总结"
}
```

- [ ] **Step 3: 创建严审清单文档**

```markdown
# 严审清单

## 检查项与标准

| # | 检查项 | 标准 | 权重 |
|---|--------|------|------|
| 1 | 态势评级 | 核爆≥90，沸腾≥75 | 20分 |
| 2 | 信源合规 | S1+S2+A级≥70% | 20分 |
| 3 | 作战地图 | 四要素完整 | 20分 |
| 4 | 风险预警 | 包含具体阈值 | 15分 |
| 5 | 利好类型 | 已标注 | 10分 |
| 6 | 关键路标 | 可验证 | 10分 |
| 7 | 热点覆盖 | 无遗漏 | 5分 |

## 审查结果分类

- **通过**: 质量分≥80，无致命问题
- **建议修改**: 无致命问题，有优化建议
- **需要修改**: 1-2个致命问题
- **严重不通过**: 3+个致命问题 或 数据质量极差
```

- [ ] **Step 4: Commit**

---

## Chunk 4: 实现主编搜索调度功能

**目标:** 在stock-editor中实现并行搜索和轻审功能

### Task 4.1: 添加搜索调度功能

**Files:**
- Modify: `C:\Users\Administrator\.claude\skills\stock-analyst-cat\stock-editor\SKILL.md`

- [ ] **Step 1: 添加搜索调度章节**

```markdown
## 搜索调度

### 并行搜索指令

在主编prompt中使用以下指令实现并行搜索：

```
## 1. 并行搜索
请同时搜索以下热点（使用mcporter）：
- 煤炭板块
- 光伏
- AI算力

## 2. 等待搜索完成
等待所有搜索返回结果
```

### 搜索结果格式

```json
{
  "hotspots": [
    {
      "name": "煤炭板块",
      "search_results": [
        {"source": "S1级", "content": "...", "timestamp": "2026-03-14"}
      ]
    }
  ]
}
```
```

- [ ] **Step 2: 添加轻审功能**

```markdown
## 轻审（30秒）

### 检查项（精简版）

```
□ 1. 是否有今日数据？（时间戳检查）
□ 2. 热点数量≥3？
```

### 轻审通过标准

- 有今日数据 且 热点数量≥3 → 继续分析
- 否则 → 标记问题，继续或跳过
```

- [ ] **Step 3: Commit**

---

## Chunk 5: 实现主编输出功能

**目标:** 在stock-editor中实现最终报告输出功能

### Task 5.1: 添加输出功能

**Files:**
- Modify: `C:\Users\Administrator\.claude\skills\stock-analyst-cat\stock-editor\SKILL.md`

- [ ] **Step 1: 添加输出章节**

```markdown
## 最终输出

### 输出格式

```markdown
🕒 分析基准时刻：[时间]
⏰ 当前阶段：[阶段]
🔥 热点发现状态：发现X个新热点
🌍 国内外联合共振状态：发现X个共振热点

---

## 💎 主题：[热点名称]

**态势评级**：⚡⚡⚡⚡沸腾级 + 【喵娘锐评】 + 【风险等级】

**🧩 关键拼图**：
* [🟢🟢S1级] / [🟢S2级] / [🔵A级] [时间]-信源：内容

**🗺️ 作战地图**：
* 核心突击位：代码 名称
* 侧翼观测位：代码 名称

**⚔️ 行动指令**：
窗口：[黄金窗口/确认窗口/观察窗口]
```

### 人工处理提示

当有热点需要人工处理时：

```
⚠️ 以下热点需要人工处理：
- 煤炭板块：审查3次未通过，原因...
- 光伏：搜索超时，缺少数据
```
```

- [ ] **Step 2: Commit**

---

## Chunk 6: 集成测试

**目标:** 验证三个skill可以正常协作

### Task 6.1: 端到端测试

- [ ] **Step 1: 创建测试场景**

测试场景：盘前扫描

输入：
```
"帮我做盘前扫描，看看今天有啥热点"
```

预期流程：
1. 主编解析场景 → pre_market
2. 主编并行搜索热点
3. 主编轻审
4. 调用分析代理分析
5. 调用审查代理审查
6. 主编输出报告

- [ ] **Step 2: 验证调用流程**

检查三个skill之间的调用是否正常：
- 主编 → 分析代理
- 主编 → 审查代理

- [ ] **Step 3: 验证超时处理**

测试超时机制是否正常工作

- [ ] **Step 4: Commit**

---

## 实施顺序

1. **Chunk 1**: stock-editor骨架 → 1小时
2. **Chunk 2**: stock-analyst骨架 → 1小时
3. **Chunk 3**: stock-reviewer骨架 → 1小时
4. **Chunk 4**: 搜索调度功能 → 1小时
5. **Chunk 5**: 输出功能 → 1小时
6. **Chunk 6**: 集成测试 → 2小时

**预计总时间**: 7小时
