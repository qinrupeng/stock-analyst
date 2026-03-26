# 工作流操作指南

> 三代理协作架构 - 规范工作流程
> 版本：1.0 (2026-03-14)

---

## 概述

本文档定义如何使用 stock-analyst-cat 的三代理架构进行A股分析。

**核心原则**：每次分析都应该依次使用三个模块的文档。

---

## 标准工作流程（7步）

```
用户输入 → 主编(解析+搜索) → 分析(深度分析) → 审查(质量把控) → 输出报告
```

### Step 1: 加载主编模块

**文件**: `stock-editor/SKILL.md`

**任务**:
- 场景解析（识别pre_market/intra_day/after_market/stock_analysis）
- 热点识别（从知识库/记忆提取）
- 并行搜索（mcporter搜索热点）
- 轻审检查（30秒快速检查）

**检查清单**:
- [ ] 场景类型已确定
- [ ] 热点列表已识别（≥3个）
- [ ] 搜索结果已获取
- [ ] 轻审通过

---

### Step 2: 加载分析模块

**文件**: `stock-analyst/SKILL.md`
**参考**: `stock-analyst/references/01-analysis.md` + `02-rating.md`

**任务**:
- 对每个热点进行深度分析
- 计算态势评级（核爆/沸腾/发酵/观望）
- 构建作战地图（核心/侧翼/路标）
- 识别风险信号

**检查清单**:
- [ ] 每个热点都有分析结果
- [ ] 态势评级已给出
- [ ] 作战地图完整
- [ ] 风险提示到位

---

### Step 3: 加载审查模块

**文件**: `stock-reviewer/SKILL.md`
**参考**: `stock-reviewer/references/02-checklist.md`

**任务**:
- 对照检查清单验证
- 计算质量分
- 给出审查结论
- 如不通过，列出修改建议

**检查清单**:
- [ ] 态势评级≥75分
- [ ] S1+S2+A级信源≥70%
- [ ] 作战地图四要素完整
- [ ] 风险预警有阈值

**审查结论**:
- ✅ 通过：质量分≥80
- ⚠️ 建议修改：无致命问题
- ❌ 需要修改：有1-2个致命问题

---

### Step 4: 输出报告

**文件**: `stock-editor/SKILL.md` - 主编输出模板

**任务**:
- 汇总所有分析结果
- 格式化输出
- 添加审查状态表
- 生成最终报告

---

## 不同场景的工作流

### 场景1: 盘前扫描 (pre_market)

```
1. 加载 stock-editor → 解析场景为 pre_market
2. 识别热点列表（煤炭/光伏/AI算力等）
3. 并行搜索热点
4. 加载 stock-analyst → 分析每个热点
5. 加载 stock-reviewer → 质量审查
6. 输出盘前热点报告
```

### 场景2: 个股分析 (stock_analysis)

```
1. 加载 stock-editor → 解析场景为 stock_analysis
2. 提取股票代码
3. 并行搜索（基本面/技术面/消息面）
4. 加载 stock-analyst → 深度分析
5. 加载 stock-reviewer → 质量审查
6. 输出个股分析报告
```

### 场景3: 收盘复盘 (after_market)

```
1. 加载 stock-editor → 解析场景为 after_market
2. 识别今日热点
3. 搜索今日数据
4. 加载 stock-analyst → 复盘分析
5. 加载 stock-reviewer → 质量审查
6. 输出复盘报告
```

---

## 文档引用速查

| 场景 | 必读文档 |
|------|----------|
| 任何 | stock-editor/SKILL.md |
| 盘前扫描 | stock-editor/references/01-scenes.md |
| 分析 | stock-analyst/SKILL.md |
| 评级 | stock-analyst/references/02-rating.md |
| 审查 | stock-reviewer/SKILL.md |
| 检查清单 | stock-reviewer/references/02-checklist.md |

---

## 常见问题

**Q: 可以跳过某些步骤吗？**
A: 不建议。审查模块是质量把控的关键环节。

**Q: 审查不通过怎么办？**
A: 记录问题，返回分析模块重新处理。

**Q: 需要多长时间？**
A: 盘前扫描约15-20分钟，个股分析约20-30分钟。

---

## 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-03-14 | 初始版本 |
