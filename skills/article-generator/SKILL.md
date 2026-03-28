---
name: article-generator
description: |
  多平台文章生成器，支持今日头条/微信公众号/小红书等平台
  自动搜索素材，分析爆款，配图生成，输出符合平台调性的高质量原创文章
MANDATORY TRIGGERS: 头条文章, 今日头条, 写头条, 生成头条文章, 头条写作, 写头条, 根据热点报告写头条, 根据分析报告写头条, 公众号文章, 微信公众号, 写公众号, 生成公众号文章
---

# 📝 多平台文章生成器

自动生成符合平台调性的高质量原创文章，支持头条/公众号双平台。

---

## 🎯 平台支持

| 平台 | 写作规范 | 排版模板 |
|------|---------|---------|
| 今日头条（toutiao） | `references/toutiao-writing.md` | — |
| 微信公众号（wechat） | `references/wechat-writing-guide.md` | `references/wechat-html-template.md` |
| 小红书（待接入） | — | — |

**激活方式**：
- 头条文章：说"写头条"或"根据热点报告写头条"
- 公众号文章：说"写公众号"或加参数`--platform wechat`

---

## 📊 平台差异速览

| 维度 | 今日头条 | 微信公众号 |
|------|---------|-----------|
| 内容长度 | 800-1500字 | 1500-2500字 |
| 用户心智 | 信息流，浅阅读 | 私域，深度阅读 |
| 生命周期 | 24小时 | 永久沉淀 |
| 核心目标 | 爆火/流量 | 沉淀/信任 |
| 风险提示 | 简单提示 | **必须明确** |

---

## 🚨 执行流程（10步）

```
□ 1. 确认需求
□ 2. 读取平台规范（根据平台读取对应writing-guide）
□ 3. 定策略
□ 4. 爆款分析（可跳过）
□ 5. 素材补充
□ 6. 确认大纲
□ 7. 写文章
□ 8. 配图生成
□ 9. 质量检查
□ 10. 输出生成
```

**核心原则**：先读规则再写，不跳步骤，不60分交差

---

## 📋 各步骤执行要点

### 第2步：读取平台规范

| 平台 | 必须读取 |
|------|---------|
| 头条 | `references/toutiao-writing.md` + `article-public-workflow.md` |
| 公众号 | `references/wechat-writing-guide.md` + `references/wechat-html-template.md` |

头条默认加载SEO，`writing-guide.md` 是头条平台规则。

### 第3步：定策略

头条：标题20-30字 + 开头100-150字 + 结尾互动引导
公众号：标题20-28字 + 共情开头 + 风险提示 + 关注引导

### 第4步：爆款分析

📌 `social-content-generator-0.1.0`（读取SKILL.md）
→ 获取：爆款逆向工程6步框架 + 钩子公式

### 第5步：素材补充

📌 `seo-content-writer-2.0.0`（读取SKILL.md）
→ 获取：关键词研究 + 内容gap分析

### 第7步：写文章

**头条**：应用 `references/toutiao-writing.md` + `article-public-workflow.md`
**公众号**：应用 `references/wechat-writing-guide.md` + `references/wechat-html-template.md`

📌 去AI痕迹：读取 `../humanizer-zh/SKILL.md`

### 第8步：配图

📌 通用：`../imagen/SKILL.md`
📌 A股股票类：`../stock-report-image/SKILL.md`（**必须用，禁止直接调用imagen**）

---

## 🚫 禁止事项（违反必罚）

**【通用】**
- ❌ 禁止跳过步骤
- ❌ 禁止省略质量检查
- ❌ 禁止出现股票代码（6位数字，如000938/300136）→ 可用名称替代
- ❌ 禁止"操作建议"标题 → 改为"主线观察"，只描述窗口状态

**【A股股票类文章】**
- 🚨 必须调用stock-report-image生成封面
- 🚨 必须先读报告内容，再匹配风格，再生成提示词

**【公众号】**
- 🚨 禁止给出具体买卖建议/止损位/仓位
- 🚨 禁止确定性承诺（"肯定涨"、"必赚"）
- 🚨 必须有明确风险提示

**【违反后果】**
- 被大爷抓包 = 写3000字检讨
- 连续2次偷懒 = 自罚停止接单1天

---

## 📦 统一输出路径

`{WORKSPACE}\reports\articles\YYYY-MM-DD\`

| 文件类型 | 命名规则 |
|----------|----------|
| 头条文章 | `头条-标题.md` |
| 公众号文章 | `公众号-标题-公众号版.html` |
| 封面图 | `封面-标题.png` |

**公众号**：直接输出HTML，符合wechat-html-template.md规范

---

## 📚 规范文件索引

| 文件 | 内容 | 适用平台 |
|------|------|---------|
| `references/article-public-workflow.md` | 公共流程（10步框架/配图/质量检查） | 所有平台 |
| `references/toutiao-writing.md` | 头条平台规则（标题/开头/结构/结尾） | 头条 |
| `references/wechat-writing-guide.md` | 公众号平台规则（合规/私域/风险提示） | 公众号 |
| `references/wechat-html-template.md` | 公众号HTML排版规范 | 公众号 |
| `references/writing-guide.md` | 头条写作指南（平台规则） | 头条 |
| `references/SEO优化指南.md` | SEO优化规则（头条必读） | 头条 |

---

## ⚡ 快速激活

**头条**：
- "生成头条文章"
- "写一篇头条文章"
- "根据盘前热点扫描写头条"

**公众号**：
- "生成公众号文章"
- "写一篇公众号文章"
- "根据盘前热点扫描写公众号文章"

---

**版本**：v6.0（2026-03-28 重构：公共流程+平台规范拆分，SKILL.md精简至~280行）
