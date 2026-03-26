# stock-analyst-cat 集成测试文档

> 验证三个Skill协作的端到端测试方案

## 测试场景

### 场景1：盘前扫描 (pre_market)

**输入**：
```
"帮我做盘前扫描，看看今天有啥热点"
```

**预期流程**：
```
1. stock-editor 接收输入
2. 场景解析 → pre_market
3. 热点识别 → 从知识库提取热点
4. 并行搜索 → mcporter搜索热点
5. 轻审 → 30秒快速检查
6. 调用 stock-analyst → 深度分析
7. 调用 stock-reviewer → 质量审查
8. 汇总输出 → 格式化报告
```

### 场景2：个股分析 (stock_analysis)

**输入**：
```
"分析一下中国卫星 600118"
```

**预期流程**：
```
1. stock-editor 接收输入
2. 场景解析 → stock_analysis
3. 提取股票代码 → 600118
4. 并行搜索 → 基本面/技术面/消息面
5. 调用 stock-analyst → 深度分析
6. 调用 stock-reviewer → 质量审查
7. 汇总输出 → 个股分析报告
```

## 测试用例

### TC-001: 场景识别

| 项目 | 内容 |
|------|------|
| 输入 | "帮我做盘前扫描" |
| 预期场景 | pre_market |
| 验证点 | 正确识别为盘前扫描 |

### TC-002: 并行搜索

| 项目 | 内容 |
|------|------|
| 场景 | 识别到3个热点 |
| 验证点 | 并行搜索返回结果 |

### TC-003: 分析代理调用

| 项目 | 内容 |
|------|------|
| 输入 | 热点"煤炭板块" + 搜索结果 |
| 预期输出 | 态势评级 + 作战地图 |
| 验证点 | stock-analyst正常返回 |

### TC-004: 审查代理调用

| 项目 | 内容 |
|------|------|
| 输入 | 分析报告 |
| 预期输出 | 质量分 + 审查结论 |
| 验证点 | stock-reviewer正常返回 |

### TC-005: 超时处理

| 项目 | 内容 |
|------|------|
| 场景 | 搜索超时 |
| 验证点 | 标记问题，继续处理 |

### TC-006: 审查不通过

| 项目 | 内容 |
|------|------|
| 场景 | 质量分<60 |
| 验证点 | 给出修改建议 |

## 测试数据

### 测试热点列表

```json
[
  {"name": "煤炭板块", "score": 85},
  {"name": "光伏", "score": 78},
  {"name": "AI算力", "score": 92}
]
```

### 测试搜索结果

```json
{
  "hotspots": [
    {
      "name": "煤炭板块",
      "search_results": [
        {"source": "S1级", "content": "陕西煤业年报预增", "timestamp": "2026-03-14"},
        {"source": "A级", "content": "动力煤价格上涨", "timestamp": "2026-03-13"}
      ]
    }
  ]
}
```

### 测试分析输出

```json
{
  "hotspot_name": "煤炭板块",
  "analysis": {
    "situation_rating": "⚡⚡⚡⚡沸腾级",
    "drive_type": "业绩驱动",
    "battle_map": {
      "core": ["601001-大同煤业"],
      "flank": ["600188-兖州煤业"],
      "roadmarks": ["03-15 业绩预告"]
    },
    "risks": [
      {"type": "回调风险", "content": "短期涨幅过大", "threshold": "涨幅>15%"}
    ]
  },
  "quality_score": 85
}
```

### 测试审查输出

```json
{
  "passed": true,
  "quality_score": 85,
  "issues": [],
  "summary": "通过，质量良好"
}
```

## 验证检查表

### 主编验证 (stock-editor)

- [ ] 场景解析正确
- [ ] 热点识别成功
- [ ] 并行搜索执行
- [ ] 轻审机制有效
- [ ] 代理调用正常
- [ ] 输出格式正确

### 分析代理验证 (stock-analyst)

- [ ] 输入接收正确
- [ ] 多维分析执行
- [ ] 态势评级准确
- [ ] 作战地图完整
- [ ] 风险评估充分
- [ ] 输出格式正确

### 审查代理验证 (stock-reviewer)

- [ ] 检查清单完整
- [ ] 质量分计算正确
- [ ] 审查结论准确
- [ ] 修改建议明确
- [ ] 输出格式正确

## 测试执行

### 手动测试

1. 输入测试场景
2. 观察流程执行
3. 验证每步输出
4. 记录问题

### 自动测试（待开发）

```python
# 测试脚本框架
def test_flow():
    # 1. 场景解析测试
    scene = parse_scene("盘前扫描")
    assert scene == "pre_market"

    # 2. 搜索调度测试
    results = parallel_search(hotspots)
    assert len(results) >= 3

    # 3. 分析代理测试
    analysis = stock_analyst.analyze(hotspot, results)
    assert analysis.situation_rating is not None

    # 4. 审查代理测试
    review = stock_reviewer.review(analysis)
    assert review.passed is not None
```

## 问题追踪

| ID | 问题 | 严重度 | 状态 |
|----|------|--------|------|
| TBD | - | - | 待发现 |

## 测试结果

| 测试项 | 状态 | 备注 |
|--------|------|------|
| TC-001 | ✅ 架构设计通过 | 场景解析逻辑已定义 |
| TC-002 | ✅ 架构设计通过 | 并行搜索协议已定义 |
| TC-003 | ✅ 架构设计通过 | 分析代理协议已定义 |
| TC-004 | ✅ 架构设计通过 | 审查代理协议已定义 |
| TC-005 | ✅ 架构设计通过 | 超时处理已定义 |
| TC-006 | ✅ 架构设计通过 | 审查循环已定义 |

## 架构验证

### 协议层 ✅

- [x] 主编 → 分析代理 调用协议
- [x] 主编 → 审查代理 调用协议
- [x] 输入输出格式标准化
- [x] 错误处理机制

### 文档层 ✅

- [x] stock-editor/SKILL.md 完整
- [x] stock-analyst/SKILL.md 完整
- [x] stock-reviewer/SKILL.md 完整
- [x] references 文档齐全

### 测试层 ✅

- [x] 测试场景定义
- [x] 模拟数据准备
- [x] 验证检查表
- [x] 执行指南
