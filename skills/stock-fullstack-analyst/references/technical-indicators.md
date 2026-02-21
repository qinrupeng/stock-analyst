# 技术指标解读标准

## 📈 趋势判断指标

### 移动平均线（MA）
```python
def analyze_ma(stock_data: dict) -> dict:
    """
    移动平均线分析
    
    核心逻辑：
    - 股价在均线上方 > 均线下方 → 短期偏强
    - 短期均线在长期均线上方 → 均线多头排列
    - 股价跌破关键均线 → 短期风险信号
    
    参数设置：
    - MA5：5日均线（周线）
    - MA10：10日均线（双周线）
    - MA20：20日均线（月线）
    - MA60：60日均线（季线）
    - MA250：250日均线（年线）
    
    信号解读：
    - MA5 > MA10 > MA20：强势多头
    - MA20 > MA60 > MA250：稳健多头
    - MA5 < MA10 < MA20：弱势空头
    """
    return {
        "ma5": float,
        "ma10": float,
        "ma20": float,
        "ma60": float,
        "ma_position": "above/below",  # 股价相对MA20位置
        "ma_trend": "bullish/bearish/neutral",
        "signal": "买入/卖出/观望"
    }
```

### 趋势通道
```python
def analyze_trend_channel(prices: list) -> dict:
    """
    趋势通道分析
    
    方法：
    - 布林带（Bollinger Bands）
    - 趋势线画线
    - 平行通道识别
    
    输出：
    {
        "upper_band": float,    # 上轨
        "middle_band": float,   # 中轨
        "lower_band": float,    # 下轨
        "bandwidth": float,     # 通道宽度
        "position": "upper/middle/lower",  # 当前价格位置
        "breakout": "up/down/none"  # 突破信号
    }
    """
```

---

## 💪 动量指标

### MACD（指数平滑移动平均线）
```python
def analyze_macd(prices: list) -> dict:
    """
    MACD分析
    
    计算方法：
    - DIF = EMA12 - EMA26
    - DEA = EMA9(DIF)
    - MACD = (DIF - DEA) × 2
    
    信号解读：
    - DIF上穿DEA（金叉）：买入信号
    - DIF下穿DEA（死叉）：卖出信号
    - MACD柱由负转正：增强买入信号
    - MACD柱由正转负：增强卖出信号
    - 零轴上方金叉：强势区域金叉（更强）
    - 零轴下方金叉：弱势区域金叉（较弱）
    
    背离分析：
    - 顶背离：价格创新高，MACD未创新高 → 预示下跌
    - 底背离：价格创新低，MACD未创新低 → 预示上涨
    """
    return {
        "dif": float,
        "dea": float,
        "macd_hist": float,
        "crossover": "golden/dead/none",  # 交叉类型
        "position": "above_zero/below_zero",  # 零轴位置
        "divergence": "top/bottom/none",  # 背离类型
        "signal": "买入/卖出/观望"
    }
```

### RSI（相对强弱指数）
```python
def analyze_rsi(prices: list, period: int = 14) -> dict:
    """
    RSI分析
    
    计算方法：
    RSI = 100 - [100 / (1 + RS)]
    RS = n日内涨幅平均值 / n日内跌幅平均值
    
    经典区间：
    - RSI > 70：超买区域 → 可能回调
    - RSI < 30：超卖区域 → 可能反弹
    - RSI = 50：多空平衡
    
    信号解读：
    - RSI从超买区回落：卖出信号
    - RSI从超卖区回升：买入信号
    - RSI突破50：趋势转强
    - RSI跌破50：趋势转弱
    
    背离：
    - 价格创新高，RSI未创新高 → 顶背离（卖出）
    - 价格创新低，RSI未创新低 → 底背离（买入）
    """
    return {
        "rsi_6": float,      # 短期RSI
        "rsi_12": float,    # 中期RSI
        "rsi_24": float,    # 长期RSI
        "overbought": bool,  # 是否超买
        "oversold": bool,    # 是否超卖
        "trend": "strong/neutral/weak",
        "signal": "买入/卖出/观望"
    }
```

### KDJ随机指标
```python
def analyze_kdj(prices: list, high: list, low: list, n: int = 9, m1: int = 3, m2: int = 3) -> dict:
    """
    KDJ分析
    
    计算方法：
    RSV = (Ct - Ln) / (Hn - Ln) × 100
    K = 2/3 × K(-1) + 1/3 × RSV
    D = 2/3 × D(-1) + 1/3 × K
    J = 3K - 2D
    
    信号解读：
    - K值上穿D值（金叉）：买入信号
    - K值下穿D值（死叉）：卖出信号
    - J值 > 100：超买区域
    - J值 < 0：超卖区域
    
    特殊信号：
    - KDJ在超卖区金叉：强烈买入
    - KDJ在超买区死叉：强烈卖出
    """
```

---

## 📊 成交量指标

### 成交量分析
```python
def analyze_volume(volumes: list, prices: list) -> dict:
    """
    成交量分析
    
    量价关系：
    - 价涨量增：健康上涨（资金流入）
    - 价涨量缩：谨慎观望（可能虚涨）
    - 价跌量增：恐慌抛售（可能见底）
    - 价跌量缩：阴跌走势（风险释放）
    
    关键信号：
    - 放量突破：有效性较高
    - 缩量突破：有效性存疑
    - 天量见天价：短期风险
    - 地量见地价：变盘信号
    """
    return {
        "volume": float,
        "volume_ma5": float,      # 5日均量
        "volume_ma10": float,      # 10日均量
        "volume_ratio": float,     # 量比
        "price_trend": "up/down/sideways",
        "volume_trend": "increasing/decreasing/stable",
        "signal": "健康/背离/观望"
    }
```

### OBV能量潮
```python
def calculate_obv(prices: list, volumes: list) -> dict:
    """
    OBV能量潮
    
    原理：
    - 价格上涨，OBV增加（资金流入）
    - 价格下跌，OBV减少（资金流出）
    
    信号：
    - OBV创新高：资金持续流入
    - OBV创新低：资金持续流出
    - OBV与股价背离：预警信号
    """
```

---

## 🎯 波动性指标

### 布林带（Bollinger Bands）
```python
def analyze_bollinger_bands(prices: list, window: int = 20, std_dev: int = 2) -> dict:
    """
    布林带分析
    
    计算方法：
    - 中轨 = MA20
    - 上轨 = 中轨 + 2×标准差
    - 下轨 = 中轨 - 2×标准差
    
    信号解读：
    - 股价突破上轨：超买信号，可能回调
    - 股价跌破下轨：超卖信号，可能反弹
    - 布林带收口：波动率降低，可能突破
    - 布林带开口：波动率增加，趋势延续
    
    操作建议：
    - 触及上轨：减仓/止盈
    - 触及下轨：加仓/抄底
    - 回归中轨：持仓待涨
    """
```

### ATR平均真实波幅
```python
def calculate_atr(high: list, low: list, close: list, period: int = 14) -> dict:
    """
    ATR波动率分析
    
    用途：
    - 设置止损位（2-3×ATR）
    - 评估股票波动性
    - 判断突破有效性
    
    解读：
    - ATR升高：波动加剧，风险增加
    - ATR降低：波动减小，风险降低
    """
```

---

## 🔄 综合技术评级

### 技术评分模型
```python
def technical_rating(stock_data: dict) -> dict:
    """
    综合技术评分
    
    评分维度：
    1. 趋势（30分）
       - 均线多头排列：+10
       - 股价在均线上方：+10
       - 趋势向上：+10
    
    2. 动能（30分）
       - MACD金叉：+10
       - RSI位于40-60区间：+10
       - KDJ金叉：+10
    
    3. 资金（20分）
       - 成交量放大：+10
       - OBV上升：+10
    
    4. 波动（20分）
       - 布林带收口后开口：+10
       - ATR适中：+10
    
    评级划分：
    - A级（85-100分）：强烈看多
    - B级（70-84分）：温和看多
    - C级（55-69分）：中性
    - D级（40-54分）：温和看空
    - E级（<40分）：强烈看空
    """
```

---

## 📋 技术分析报告模板

### 技术面概览
```
┌─────────────────────────────────────────────┐
│ 技术分析评级：B+（温和看多）                   │
├─────────────────────────────────────────────┤
│ 趋势评分：8.5/10                             │
│   • 短期趋势：震荡上行                        │
│   • 中期趋势：均线多头排列                     │
│   • 长期趋势：上升通道                        │
├─────────────────────────────────────────────┤
│ 动能评分：7.5/10                             │
│   • MACD：零轴上方金叉                        │
│   • RSI：58（偏强区域）                       │
│   • KDJ：K值上穿D值                           │
├─────────────────────────────────────────────┤
│ 资金评分：8.0/10                             │
│   • 量价配合：价涨量增（健康）                 │
│   • OBV：持续上升                            │
├─────────────────────────────────────────────┤
│ 风险评分：7.0/10                             │
│   • 波动率：适中                             │
│   • 支撑位：XX.XX元                          │
│   • 阻力位：XX.XX元                          │
└─────────────────────────────────────────────┘
```

### 操作建议
```
当前价格：XX.XX元

买入时机：
• 回调至MA20（XX.XX元）附近企稳
• 或突破箱体上沿（XX.XX元）后回踩确认

止损位：
• 跌破MA60（XX.XX元）止损
• 或亏损达到8%止损

目标位：
• 第一目标：XX.XX元（+XX%）
• 第二目标：XX.XX元（+XX%）

仓位建议：
• 激进型：30-50%
• 稳健型：20-30%
• 保守型：10-20%
```
