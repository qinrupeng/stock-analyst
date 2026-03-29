---
name: stock-report-image
description: |
  A股热点报告/今日头条/微信公众号股票类文章专属配图生成器。从A股报告或股票类文章自动提取主题，生成对应风格的AI配图/封面。
  【仅用于股票报告股票文章，今日头条、微信公众号股票类内容的配图需求】通用生图需求请使用imagen技能。
  核心功能：读取报告/文章→智能分析主题→自动匹配风格→逐格精确定义提示词→调用imagen生成专属封面
  【依赖要求】必须先安装imagen技能才能正常使用
MANDATORY TRIGGERS: 报告配图, 热点配图, 盘前配图, 盘中配图, 头条配图, 头条封面, 微信公众号配图, 微信公众号封面, 股票文章配图, 股票封面图
---

# A股配图生成器

> **核心功能**：读取报告 → 智能分析主题 → 逐格精确定义 → 生成1张封面
> **赛道风格/图标/布局**：全部在 `config/styles_config.yaml` 维护（单一配置源）

---

## 使用方式

```bash
# 自动模式（读取最新报告 → 生成封面）
python scripts/generate_cover.py --cover

# 指定报告
python scripts/generate_cover.py --cover --report 2026-03-25-盘前扫描.md

# 指定风格（可选）
python scripts/generate_cover.py --cover --style folder

# 指定布局（大爷最爱：top3_bottom2）
python scripts/generate_cover.py --cover --layout top3_bottom2

# 仅生成提示词（不调用imagen）
python scripts/generate_cover.py --cover --prompt-only

# 适配公众号平台（自动2.35:1比例+标题规则）
python scripts/generate_cover.py --cover --platform wechat --title "五大热点机会"
```

---

## 配置索引（单一来源：config/styles_config.yaml）

| 配置项 | 位置 | 说明 |
|--------|------|------|
| 赛道→风格映射 | `theme_styles` | 修改赛道风格来这里 |
| 赛道→图标映射 | `stock_topic_slot_icons`（73个） | 修改赛道图标来这里 |
| 风格→参考图映射 | `style_ref_map` | 修改风格参考图来这里 |
| 布局推荐策略 | `layout_by_topic_count` | 按赛道数量自动选布局 |
| 5赛道可选布局 | `five_topic_layouts` | 大爷最爱top3_bottom2 |
| folder风格描述 | `folder_style_desc` | 大爷验证的folder风格精确描述 |
| 公众号标题规则 | `wechat_cover_rules` | 标题字数/禁止词/模板 |
| 布局视觉定义 | `layout_definitions` | 各布局的文字描述 |

---

## 赛道风格分类（简览）

| 风格 | 适用赛道 |
|------|---------|
| **folder ⭐** | 储能/储能锂电/锂电/电池/光伏/电力/电网/特高压/新能源/投资机会 |
| **blueprint_lab** | 算力/芯片/AI/半导体/光模块/存储芯片/PCB/消费电子/商业航天/低空/脑机接口/可控核聚变/机器人/具身智能 |
| **retro_pop_grid** | 黄金/铜/稀土/小金属/战略金属/钨/锂/镍/有色金属 |
| **vintage_journal** | 医药/创新药/CXO/磷化工/化肥/军工 |
| **archive** | 金融/银行 |

---

## 布局选项

| 赛道数量 | 默认布局 | 可选布局 |
|---------|---------|---------|
| 5个 | top3_bottom2 ⭐ | hub_spoke / left4_right1 / fan_shaped |
| 6个 | grid_2x3 | - |
| 4个 | grid_2x2 | - |
| 3个 | three_column | - |
| 2个 | two_column | - |

**top3_bottom2 = 顶部3格横排 + 底部2格横排**（大爷最爱，均衡对称）

---

## 参考图目录

> ⚠️ `xhs-images-layouts/` 目录已废弃，请勿使用

完整中文索引：`参考图目录.md`（收录97张参考图）

| 目录 | 图片数 | 用途 |
|------|--------|------|
| cover-image-styles/ | 13张 | 封面参考图 |
| article-illustrator-styles/ | 16张 | 文章插图 |
| infographic-styles/ | 37张 | 信息图 |
| slide-deck-styles/ | 14张 | PPT幻灯片 |
| xhs-images-styles/ | 17张 | 小红书风格 |

---

## 输出目录

```
D:\AI_Workspace\reports\images\stock-covers\YYYY-MM-DD\
└── timestamp_cover_XX主题.png  # 封面图
    └── refs/                    # 参考图副本
```
