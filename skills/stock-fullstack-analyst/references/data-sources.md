# 数据源配置与调用规范

## 🌐 Browser实时抓取配置

### 股票实时数据
```javascript
{
  dataType: "realtime_price",
  sources: [
    { name: "东方财富", url: "https://quote.eastmoney.com/{code}.html", priority: 1 },
    { name: "同花顺", url: "https://quote.10jqka.com.cn/{code}/", priority: 2 }
  ],
  fields: ["current_price", "change_percent", "volume", "turnover", "high", "low", "open"]
}
```

### 财务指标数据
```javascript
{
  dataType: "financial_indicators",
  sources: [
    { name: "同花顺", url: "https://basic.10jqka.com.cn/{code}/", priority: 1 },
    { name: "新浪财经", url: "https://finance.sina.com.cn/realstock/company/{code}/nc.shtml", priority: 2 }
  ],
  fields: ["pe", "pb", "roe", "market_cap", "revenue", "net_profit"]
}
```

### 资金流向数据
```javascript
{
  dataType: "fund_flow",
  sources: [
    { name: "东方财富", url: "https://data.eastmoney.com/zlsj/_{code}.html", priority: 1 }
  ],
  fields: ["main_net_inflow", "north_net_inflow", "foreign_net_inflow"]
}
```

### 技术指标数据
```javascript
{
  dataType: "technical_indicators",
  sources: [
    { name: "通达信网页", url: "https://quote.tdx.com.cn/quote/{code}.html", priority: 1 }
  ],
  fields: ["macd", "rsi", "ma", "boll", "kdj"]
}
```

---

## 🔍 MCP工具调用规范

### 舆情分析
```python
def analyze_sentiment(stock_code: str) -> dict:
    """
    分析股票舆情热度与情绪倾向
    
    Args:
        stock_code: 股票代码或名称
    
    Returns:
        {
            "sentiment_score": 0-100,  # 舆情热度
            "sentiment_type": "positive/negative/neutral",
            "news_count": int,          # 分析新闻数
            "key_topics": [str],        # 热点话题
            "update_time": str          # 更新时间
        }
    """
```

### 热点资讯搜索
```python
def search_hot_news(stock_code: str, days: int = 7) -> list:
    """
    搜索股票相关热点新闻
    
    Args:
        stock_code: 股票代码或名称
        days: 回溯天数
    
    Returns:
        [{
            "title": str,           # 新闻标题
            "source": str,          # 新闻来源
            "time": str,           # 发布时间
            "sentiment": str,      # 情绪分类
            "url": str             # 新闻链接
        }]
    """
```

### 行业动态分析
```python
def analyze_industry_trends(industry: str) -> dict:
    """
    分析行业发展趋势与驱动因素
    
    Returns:
        {
            "industry_trends": [str],
            "growth_drivers": [str],
            "risk_factors": [str],
            "market_outlook": str
        }
    """
```

---

## 📊 数据标注规范

### 来源标识格式
```html
<!-- Browser抓取 -->
<span class="source" data-type="browser" data-source="东方财富" data-time="14:30">
    Browser抓取·东方财富·更新于14:30
</span>

<!-- MCP搜索 -->
<span class="source" data-type="mcp" data-source="新闻搜索" data-time="14:35">
    MCP新闻搜索·{关键词}·更新于14:35
</span>

<!--用户提供 -->
<span class="source" data-type="user">
    用户提供
</span>

<!-- 估算数据 -->
<span class="source" data-type="inferred">
    基于行业估算
</span>
```

---

## 🔄 数据更新策略

### 实时数据（每分钟更新）
- 当前股价、涨跌幅
- 成交量、成交额
- 资金流向（主力/北向）

### 准实时数据（每小时更新）
- 舆情热度
- 热点新闻聚合
- 技术指标计算值

### 日更数据（每日收盘后更新）
- 财务指标
- 行业对比数据
- ESG评分

---

## ✅ 数据验证机制

### 多源交叉验证
```python
def validate_price(stock_code: str) -> dict:
    """
    交叉验证股价数据
    
    Returns:
        {
            "price": float,           # 验证后的价格
            "confidence": "high/medium/low",
            "sources": {
                "eastmoney": float,
                "tonghuashun": float,
                "deviation": float     # 各数据源偏差
            }
        }
    """
```

### 异常数据处理
- 偏差超过5%：标记为"⚠️数据存疑"
- 数据缺失：标注"暂无数据"
- 数据超时（>1小时）：标注"⚠️数据可能过时"

---

## 📈 数据源健康检查

```python
HEALTH_CHECK_STATUS = {
    "browser_services": {
        "东方财富": "online/offline",
        "同花顺": "online/offline",
        "通达信": "online/offline"
    },
    "mcp_tools": {
        "新闻搜索": "online/offline",
        "情绪分析": "online/offline",
        "舆情监控": "online/offline"
    }
}
```

---

## 🎯 数据获取优先级

| 数据类型 | 首选 | 备选1 | 备选2 |
|---------|------|-------|-------|
| 实时股价 | 东方财富 | 同花顺 | 用户提供 |
| 财务指标 | 同花顺 | 新浪财经 | 估算 |
| 资金流向 | 东方财富 | 同花顺 | — |
| 技术指标 | 通达信网页 | MCP技术指标 | — |
| 舆情分析 | MCP情绪分析 | 雪球热帖 | — |
| 行业动态 | MCP搜索 | Browser行业页 | — |
| ESG评分 | Browser专业网站 | MCP ESG API | 估算 |

---

## ⚡ 调用频率限制

### Browser抓取
- 单个URL：每秒最多1次
- 总请求：每分钟最多60次

### MCP工具
- 新闻搜索：每分钟最多30次
- 情绪分析：每分钟最多20次
- 行业分析：每分钟最多10次

---

## 🔒 数据安全规范

1. **不缓存敏感数据**：实时股价等不永久存储
2. **来源可追溯**：每个数据点必须标注完整来源
3. **更新时间透明**：所有数据标注具体更新时间
4. **置信度评估**：核心数据提供置信度评分
