# 测试模拟数据

> 用于集成测试的模拟数据

## 场景1：盘前扫描

### 输入

```
"帮我做盘前扫描，看看今天有啥热点"
```

### 热点列表（模拟）

```json
[
  {"name": "煤炭板块", "score": 88},
  {"name": "光伏", "score": 82},
  {"name": "AI算力", "score": 91}
]
```

### 搜索结果（模拟）

```json
{
  "煤炭板块": [
    {"source": "S1级", "content": "陕西煤业：2025年净利润预增50%", "timestamp": "2026-03-14"},
    {"source": "S1级", "content": "国家能源局：煤炭保供政策延续", "timestamp": "2026-03-13"},
    {"source": "A级", "content": "动力煤期货价格上涨3%", "timestamp": "2026-03-13"}
  ],
  "光伏": [
    {"source": "S1级", "content": "十四五光伏装机规划上调", "timestamp": "2026-03-14"},
    {"source": "A级", "content": "硅料价格企稳回升", "timestamp": "2026-03-13"}
  ],
  "AI算力": [
    {"source": "S1级", "content": "国家算力基础设施规划发布", "timestamp": "2026-03-14"},
    {"source": "S2级", "content": "多家云厂商大幅采购AI芯片", "timestamp": "2026-03-13"},
    {"source": "A级", "content": "AI大模型商用加速", "timestamp": "2026-03-12"}
  ]
}
```

### 分析结果（stock-analyst输出）

```json
{
  "hotspot_name": "煤炭板块",
  "analysis": {
    "situation_rating": "⚡⚡⚡⚡沸腾级",
    "drive_type": "多重驱动（政策+业绩）",
    "score_breakdown": {
      "消息面": 38,
      "市场预期": 30,
      "情绪驱动": 20,
      "加分项": 5,
      "减分项": 5
    },
    "battle_map": {
      "core": [
        {"code": "601001", "name": "大同煤业"},
        {"code": "601225", "name": "陕西煤业"}
      ],
      "flank": [
        {"code": "600188", "name": "兖州煤业"},
        {"code": "600395", "name": "盘江股份"}
      ],
      "roadmarks": [
        {"time": "03-15", "event": "业绩预告密集发布"},
        {"time": "03-20", "event": "采暖季结束"}
      ]
    },
    "risks": [
      {
        "type": "回调风险",
        "content": "短期涨幅已大，注意回调",
        "threshold": "涨幅>15%",
        "mitigation": "可适当减仓"
      }
    ]
  },
  "quality_score": 88
}
```

### 审查结果（stock-reviewer输出）

```json
{
  "passed": true,
  "quality_score": 88,
  "issues": [
    {
      "type": "建议",
      "severity": "low",
      "location": "风险提示",
      "problem": "可增加政策风险提示",
      "suggestion": "考虑添加进口煤政策变化风险"
    }
  ],
  "summary": "通过，质量良好，建议优化风险提示"
}
```

## 场景2：个股分析

### 输入

```
"分析一下中国卫星 600118"
```

### 搜索结果（模拟）

```json
{
  "基本面": [
    {"source": "S1级", "content": "2025年营收增长15%", "timestamp": "2026-03-10"},
    {"source": "A级", "content": "卫星互联网订单充足", "timestamp": "2026-03-12"}
  ],
  "技术面": [
    {"source": "A级", "content": "突破年线压力", "timestamp": "2026-03-13"},
    {"source": "B级", "content": "MACD金叉", "timestamp": "2026-03-13"}
  ],
  "消息面": [
    {"source": "S1级", "content": "北斗三号全面组网完成", "timestamp": "2026-03-14"}
  ]
}
```

### 分析结果

```json
{
  "hotspot_name": "中国卫星",
  "analysis": {
    "situation_rating": "⚡⚡⚡⚡沸腾级",
    "drive_type": "多重驱动（政策+业绩+技术）",
    "battle_map": {
      "core": [
        {"code": "600118", "name": "中国卫星"}
      ],
      "flank": [
        {"code": "002151", "name": "北斗星通"},
        {"code": "300698", "name": "万通发展"}
      ],
      "roadmarks": [
        {"time": "03-20", "event": "北斗应用大会"},
        {"time": "04-15", "event": "一季报发布"}
      ]
    },
    "risks": [
      {
        "type": "估值风险",
        "content": "当前PE偏高",
        "threshold": "PE>60",
        "mitigation": "等待回调"
      }
    ]
  },
  "quality_score": 85
}
```

## 审查清单验证

| 检查项 | 煤炭板块 | 光伏 | AI算力 | 中国卫星 |
|--------|----------|------|--------|----------|
| 态势评级≥75 | ✅ 88 | ✅ 82 | ✅ 91 | ✅ 85 |
| S+A≥70% | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% |
| 作战地图完整 | ✅ | ✅ | ✅ | ✅ |
| 风险预警 | ✅ | ✅ | ✅ | ✅ |
| 利好类型标注 | ✅ | ✅ | ✅ | ✅ |
| 关键路标 | ✅ | ✅ | ✅ | ✅ |

## 测试结论

| 场景 | 通过 | 备注 |
|------|------|------|
| 盘前扫描 | ✅ | 三热点全部通过 |
| 个股分析 | ✅ | 审查通过 |
