# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## 搜索引擎配置（重要！）
**web_search 工具（Brave API）未配置 API Key，不可用。**

所有网页搜索必须通过 MCP：
```bash
# 中文搜索（主查询）
mcporter call aliyunWebSearch.bailian_web_search query="搜索关键词" count=5 --output json
mcporter call aliyWebSearch.bailian_web_search query="搜索关键词" count=10 --output json
mcporter call MiniMax.web_search query="搜索关键词" --output json

# 英文搜索
mcporter call tavily.tavily_search query="关键词" --output json
mcporter call bochaWebSearch.BochaWebSearch query="关键词" --output json
```

**已测试可用的搜索工具：**
| 工具 | 工具名 | 用途 | 状态 |
|------|--------|------|------|
| aliyunWebSearch | bailian_web_search | 中文主查询 | 推荐 |
| aliyWebSearch | bailian_web_search | 中文主查询 | 推荐 |
| MiniMax | web_search | 中文主查询 | 可用 |
| tavily | tavily_search | 英文查询 | 可用 |
| bochaWebSearch | BochaWebSearch | 英文查询 | 可用 |

### 使用规则
- 中文搜索 → aliyunWebSearch（首选）、aliyWebSearch（次选）、MiniMax（备用）
- 英文搜索 → tavily（首选）、bochaWebSearch（备用）

调用方式：用 `exec` 工具执行上述命令，timeout 建议 30s。可以并行调用多个搜索。

## 图像识别 MCP

```bash
# MiniMax 图像理解（推荐使用skill）
mcporter call MiniMax.understand_image prompt="分析要求" image_source="图片URL或base64" --output json

# 使用 skill（自动调用上述命令）
# 直接说"分析这张图片"即可
```

---

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## 盯盘数据源（v5.0大更新）

### 数据源优先级（已实测验证✅）
| 数据 | 首选 | 备选 | 准确度 |
|------|------|------|--------|
| 实时价格/PE/换手/市值 | **腾讯财经qt.gtimg.cn** | Browser东方财富 | ✅ 100% |
| 资金流 | Browser东方财富 | — | ✅ |
| 消息面/研报 | Browser东方财富 | — | ✅ |
| 技术指标 | 东方财富API | — | ⚠️ 公式可算 |
| 大盘指数 | 东方财富API | — | ✅ |

### 腾讯财经接口（★首选，Referer随意但要有）
```bash
# 深圳: sz  上海: sh
Invoke-RestMethod -Uri "https://qt.gtimg.cn/q=sz301308" -Headers @{"Referer"="https://gu.qq.com"}
# 返回: v_sz301308="51~名称~代码~现价~昨收~今开~成交量~外盘~内盘~..."
# 字段47=总市值(万)，字段48=流通市值(万)，÷10000=亿
```

### 已废弃数据源
- ❌ 新浪财经hq — 字段解析歧义，昨收/今开容易搞反
- ❌ 东方财富API f169/f170/f174 — 基准错误或数据失真
- ❌ 雪球API — 需要签名，无法自动化

### 详细规范
见: `D:\AI_Workspace\tools\stock_watch_template_v2.md` (v5.0)

---

Add whatever helps you do your job. This is your cheat sheet.
