# 估值分析详细框架

## 📊 相对估值方法

### PE估值（市盈率）
```python
def calculate_pe_valuation(stock_data: dict) -> dict:
    """
    计算PE估值
    
    公式：PE = 股价 / 每股收益(EPS)
    
    分析维度：
    1. 与历史PE对比（当前所处分位）
    2. 与行业PE对比（估值溢价/折价）
    3. 与可比公司对比
    4. PEG = PE / 净利润增长率
       - PEG < 1：相对低估
       - PEG = 1：合理
       - PEG > 1：相对高估
    """
    return {
        "pe_ttm": float,       # TTM市盈率
        "pe_lfy": float,       # 静态市盈率
        "pe_fwd": float,       # 动态市盈率
        "pe_percentile": float,  # 历史分位(%)
        "industry_avg_pe": float, # 行业平均PE
        "peg_ratio": float,    # PEG比率
        "valuation_status": "高估/合理/低估"
    }
```

### PB估值（市净率）
```python
def calculate_pb_valuation(stock_data: dict) -> dict:
    """
    计算PB估值
    
    公式：PB = 股价 / 每股净资产(BPS)
    
    分析维度：
    1. 与历史PB对比
    2. 与行业PB对比
    3. ROE与PB关系：PB ≈ ROE × PE
    
    适用场景：
    - 周期股（PB比PE更稳定）
    - 银行、地产等重资产行业
    - 盈利波动大的公司
    """
```

### PS估值（市销率）
```python
def calculate_ps_valuation(stock_data: dict) -> dict:
    """
    计算PS估值
    
    公式：PS = 市值 / 营业收入
    
    适用场景：
    - 亏损企业（PE无意义）
    - 营收稳定但盈利波动大
    - 互联网、高增长公司
    """
```

### EV/EBITDA估值
```python
def calculate_ev_ebitda(stock_data: dict) -> dict:
    """
    计算EV/EBITDA
    
    公式：EV/EBITDA = 企业价值 / 息税折旧摊销前利润
    
    优点：
    - 剔除资本结构影响
    - 剔除税收政策影响
    - 适用于重资产行业
    """
```

---

## 💰 绝对估值方法（DCF模型）

### DCF模型核心公式
```
企业价值 = Σ [ FCF_t / (1+WACC)^t ] + TV / (1+WACC)^n

其中：
- FCF_t: 第t年自由现金流
- WACC: 加权平均资本成本
- TV: 终值（永续价值）
- n: 预测期（通常5-10年）
```

### 关键参数设置

#### 1. 自由现金流预测
```python
def project_fcf(company_data: dict, years: int = 5) -> list:
    """
    预测未来自由现金流
    
    步骤：
    1. 分析历史营收增长率
    2. 预测未来营收增长（分阶段）
    3. 预测毛利率变化趋势
    4. 预测费用率变化
    5. 计算FCF = 净利润 + D&A - CapEx - ΔWC
    """
    
    # 预测增长率分阶段
    growth_rates = {
        "phase_1": {"years": 1-2, "rate": "15-20%"},  # 短期高增长
        "phase_2": {"years": 3-5, "rate": "10-15%"},  # 中期稳健增长
        "terminal": {"rate": "3-5%"}                  # 永续增长率
    }
```

#### 2. WACC计算
```python
def calculate_wacc(company_data: dict) -> float:
    """
    计算加权平均资本成本
    
    公式：WACC = (E/V) × Ke + (D/V) × Kd × (1-T)
    
    其中：
    - E/V: 股权价值占总价值比例
    - D/V: 债务价值占总价值比例
    - Ke: 股权资本成本（CAPM模型）
    - Kd: 债务资本成本
    - T: 所得税率
    
    CAPM模型：Ke = Rf + β × (Rm - Rf)
    
    参数参考：
    - Rf（无风险利率）：2.5-3.5%（10年期国债）
    - Rm-Rf（市场风险溢价）：4-6%
    - β（贝塔系数）：0.8-1.2（行业均值）
    """
    pass
```

#### 3. 终值计算
```python
def calculate_terminal_value(fcf_n: float, g: float, wacc: float) -> float:
    """
    计算永续价值（终值）
    
    公式：TV = FCF_n × (1+g) / (WACC - g)
    
    参数：
    - FCF_n: 预测期最后一年自由现金流
    - g: 永续增长率（通常3-5%）
    - WACC: 加权平均资本成本
    
    注意：WACC必须大于g，否则模型失效
    """
```

### DCF估值输出模板
```python
dcf_result = {
    "intrinsic_value": float,           # 内在价值
    "value_range": {                     # 估值区间
        "optimistic": float,            # 乐观情景
        "base_case": float,             # 基准情景
        "pessimistic": float            # 悲观情景
    },
    "key_assumptions": {
        "revenue_growth_rate": "10-15%",
        "wacc": "8-10%",
        "terminal_growth": "3-4%",
        "operating_margin_improvement": "+2%"
    },
    "valuation_multiple": {
        "current_pe": "XX倍",
        "dcf_implied_pe": "XX倍",
        "upside_potential": "+/-XX%"
    },
    "sensitivity_analysis": {
        "wacc_sensitivity": {
            "-1%": "+XX%估值",
            "base": "基准估值",
            "+1%": "-XX%估值"
        },
        "growth_sensitivity": {
            "+2%营收增长": "+XX%估值",
            "base": "基准估值",
            "-2%营收增长": "-XX%估值"
        }
    }
}
```

---

## 🎯 估值结论框架

### 估值比较表
| 估值方法 | 估值结果 | 对应股价 | 评价 |
|---------|---------|---------|------|
| PE估值（行业平均） | XX倍 | XX.XX元 | 合理 |
| PE估值（历史中枢） | XX倍 | XX.XX元 | 合理 |
| PB估值 | XX倍 | XX.XX元 | 合理 |
| DCF估值（基准） | — | XX.XX元 | 合理 |
| **综合估值** | — | **XX.XX元** | **合理/低估/高估** |

### 估值决策矩阵
| 当前估值 | 隐含回报率 | 操作建议 |
|---------|-----------|---------|
| 较内在价值折价>20% | >25% | 强烈买入 |
| 较内在价值折价10-20% | 15-25% | 买入 |
| 较内在价值折价0-10% | 5-15% | 增持 |
| 接近内在价值 | 0-5% | 持有 |
| 较内在价值溢价>10% | <0 | 减持 |
| 较内在价值溢价>30% | 负回报 | 清仓 |

---

## 📈 敏感性分析

### 单因素敏感性分析
```python
def sensitivity_analysis(base_value: float, factor: str, changes: list) -> dict:
    """
    单因素敏感性分析
    
    Args:
        base_value: 基准估值
        factor: 敏感因素（营收增速/毛利率/WACC/永续增长率）
        changes: 变化幅度列表
    
    Returns:
        {
            "factor": "营收增速",
            "base_case": 10%,
            "results": {
                "-5%": {"new_value": float, "change": "%"},
                "-2%": {"new_value": float, "change": "%"},
                "0%": {"new_value": float, "change": "%"},
                "+2%": {"new_value": float, "change": "%"},
                "+5%": {"new_value": float, "change": "%"}
            }
        }
    """
```

### 多因素敏感性分析
```python
def multi_factor_analysis() -> dict:
    """
    多因素敏感性分析
    
    矩阵形式展示：
    
    营收增速\WACC    7%      8%      9%
    -----------|------------------------
    8%          | 52元   45元   40元
    10%         | 58元   50元   44元
    12%         | 65元   56元   49元
    
    结论：
    - 基准情景（WACC=8%, 营收增速=10%）：50元
    - 乐观情景（WACC=7%, 营收增速=12%）：65元（+30%）
    - 悲观情景（WACC=9%, 营收增速=8%）：40元（-20%）
    """
```

---

## 🔍 估值陷阱识别

### 需要调整PE的情形
1. **会计政策变更**：重述历史PE
2. **一次性损益**：使用调整后净利润
3. **周期顶点**：使用周期调整PE（CAPE）
4. **高增长阶段**：使用PEG而非绝对PE

### 需要调整DCF的情形
1. **财务杠杆剧变**：调整WACC计算
2. **重大资产重组**：重新预测现金流
3. **行业结构性变化**：调整永续增长率假设

---

## 📊 估值报告模板

### 估值概览
```
┌─────────────────────────────────────────────┐
│ 估值分析总结                                  │
├─────────────────────────────────────────────┤
│ 当前股价：XX.XX元                            │
│ 综合估值：XX.XX元（DCF + 相对估值平均）        │
│ 上涨空间：+/-XX.X%                           │
│ 估值评级：【买入/增持/中性/减持/卖出】          │
├─────────────────────────────────────────────┤
│ 关键假设：                                     │
│ • 营收CAGR：XX%（未来5年）                    │
│ • WACC：X.X%                                 │
│ • 永续增长率：X.X%                            │
│ • 目标PE：XX倍（基于行业平均）                 │
└─────────────────────────────────────────────┘
```
