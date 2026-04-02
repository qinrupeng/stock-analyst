---
name: premarket-hotcold
description: 盘前热冷记忆快取收集。触发时机：8:50 cron自动执行，或大爷说"盘前快取"。
---

# 盘前热冷记忆·快取收集

## 触发词
- "盘前快取"
- 8:50 cron自动触发
- 被stock-analyst-cat SKILL.md步骤3.5兜底调用（仅数据层）

## 执行步骤

### 第1步：检查快取是否存在且完整
```
路径：D:\AI_Workspace\tools\premarket_cache\cache\{今日日期}_cache.json
```
- 如果文件存在且 status=success → 输出"今日快取已就绪"，**结束**
- 如果文件不存在 → 执行步骤2
- **如果文件存在但 status=partial/failed，或者关键字段为 pending_browser → 强制重新抓取（步骤2）**

> ⚠️ 手动触发时即使快取存在也强制刷新，避免用残缺数据。

### 第2步：执行快取抓取
执行Python脚本：
```bash
python "D:\AI_Workspace\tools\premarket_cache\fetch_all.py"
```

**如果返回status=partial/failed或pending_browser**，立即用Browser补抓：
```bash
# 北向资金
browser(action="navigate", url="https://data.eastmoney.com/hsgtcg/")
browser(action="snapshot", compact=True)

# 东方财富资讯
browser(action="navigate", url="https://www.eastmoney.com/")
browser(action="snapshot", compact=True)
```
将Browser抓取结果手动写入 cache.json 对应字段，并更新 status。

### 第3步：输出汇总
汇总结果输出到飞书群：
- 快取抓取状态（已就绪/抓取完成）
- 北向资金（mx-data实时，单位：百万）
- 资讯数量（mx-search实时）
- 关键警告（如有pending_browser项）

## 数据来源
- **北向资金**：mx-data（东方财富妙想），单位=百万
- **资讯**：mx-search（东方财富妙想），实时搜索
- **外围美股**：新浪 gb_dji/gb_ixic（昨晚收盘价）
- **大宗商品**：NYMEX 23:00-14:30北京时间交易时段
- **A股指数**：腾讯 qt.gtimg.cn

## mx-api每日调用限制
- mx-data：每日50次（本快取任务用1次）
- mx-search：每日50次（本快取任务用1次）
- 剩余次数留给人工任务和分析使用

## 兜底机制
> 此skill可被stock-analyst-cat SKILL.md步骤3.5兜底调用。当9:00 cron触发时，如果8:50 cron missed导致快取文件不存在，步骤3.5会自动调用本skill补救。
