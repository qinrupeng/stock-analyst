---
name: stock-report-image
description: |
  A股热点报告/今日头条股票文章专属配图生成器。从A股报告或股票类文章自动提取主题，生成对应风格的AI配图/封面。
  【仅用于股票报告，今日头条、微信公众号股票类内容的配图需求】通用生图需求请使用imagen技能。
  核心功能：读取报告/文章→智能分析主题→自动匹配风格→逐格精确定义提示词→调用imagen生成专属封面
  【依赖要求】必须先安装imagen技能才能正常使用
MANDATORY TRIGGERS: 报告配图, 热点配图, 盘前配图, 盘中配图, 头条配图, 头条封面, 微信公众号配图, 微信公众号封面, 股票文章配图, 股票封面图
---

# A股配图生成器

> **核心功能**：读取报告 → 智能分析主题 → 逐格精确定义 → 生成1张封面
> **激活关键词**：配图、生成封面、报告配图、生图、封面图

基于A股热点报告自动生成封面，提示词格式经过大爷验证最优（逐格精确定义+全中文）。

---

## 核心工作流程

```
热点报告 → 提取赛道主题 → 匹配风格 → 匹配赛道图标 → 生成逐格提示词 → AI生图
```

---

## 使用方式

```bash
# 自动模式（读取最新报告 → 生成封面）
python scripts/generate_cover.py --cover

# 指定报告
python scripts/generate_cover.py --cover --report 2026-03-25-盘前扫描.md

# 指定风格（可选）
python scripts/generate_cover.py --cover --style folder

# 指定布局（可选）
python scripts/generate_cover.py --cover --layout top3_bottom2

# 仅生成提示词（不调用imagen）
python scripts/generate_cover.py --cover --prompt-only
```

---

## 赛道主题 → 风格映射

| 赛道关键词 | 推荐风格 | 说明 |
|-----------|---------|------|
| 算力/芯片/AI/半导体 | blueprint_lab | 科技蓝图风 |
| 电力/电网/特高压/光伏 | blueprint_lab | 科技蓝图风 |
| 航天/卫星/火箭/商业航天 | blueprint_lab | 科技蓝图风 |
| 脑机接口/低空经济/光模块 | blueprint_lab | 科技蓝图风 |
| 存储芯片/PCB/消费电子 | blueprint_lab | 科技蓝图风 |
| 可控核聚变 | blueprint_lab | 科技蓝图风 |
| 钨/稀土/小金属/黄金/铜 | retro_pop_grid | 复古网格风 |
| 磷化工/化肥/医药 | vintage_journal | 复古期刊风 |
| 金融/银行 | archive | 档案风 |
| 锂电/电池/储能 | acid_block | 赛博朋克风 |
| 投资机会/赛道机会/热点前瞻 | **folder** ⭐ | **文件夹风格（大爷最爱）** |

---

## 赛道图标映射（35个赛道）

赛道图标已配置化，全在 `config/styles_config.yaml` 的 `stock_topic_slot_icons` 中维护：

| 赛道 | 图标 | 赛道 | 图标 |
|------|------|------|------|
| AI数字经济 | 电路板+芯片 | 量子通信 | 原子轨道+纠缠光束 |
| 有色金属 | 金矿+金属晶体 | 深海科技 | 海浪+潜水器 |
| 储能锂电 | 太阳能板+电池 | 投资机会 | 上涨箭头+K线 |
| 黄金 | 金块+金币 | 铜 | 铜块+电缆 |
| 稀土 | 稀土矿石+发光晶体 | 机器人 | 人形机器人+机械臂 |
| 算力 | GPU芯片+服务器 | 芯片 | 方形芯片+针脚 |
| 航天 | 商业火箭+卫星星座 | 医药 | 药瓶+分子结构 |
| 光伏 | 光伏板+阳光 | 电网 | 电塔+电网 |
| 银行 | 银行大楼+钱币 | 油气 | 石油钻井+输油管道 |
| 航运 | 集装箱货轮+港口 | 脑机接口 | 大脑+电波信号+神经节点 |
| 低空经济 | 无人机+垂直起降 | 商业航天 | 商业火箭+卫星星座 |
| 光模块 | 光纤接口+光模块 | 存储芯片 | 存储芯片+数据流 |
| 创新药 | DNA双螺旋+药物分子 | 军工 | 战斗机+盾牌 |
| PCB | 印制电路板+焊接点 | 消费电子 | 折叠屏手机+AI芯片 |
| 可控核聚变 | 等离子体环+能量球 | CXO | 实验室瓶+合同文件 |

---

## 布局选项（按赛道数量自动选择）

| 赛道数量 | 默认布局 | 可选布局 |
|---------|---------|---------|
| 5个 | hub_spoke（环形放射） | **top3_bottom2**（大爷最爱）、left4_right1、fan_shaped |
| 6个 | grid_2x3（六宫格） | - |
| 4个 | grid_2x2 | - |
| 3个 | three_column | - |
| 2个 | two_column | - |

**布局说明：**
- `top3_bottom2`：顶部3格横排 + 底部2格横排，均衡对称，**大爷最爱**
- `hub_spoke`：5个面板围绕中心，环形放射
- `left4_right1`：左侧4格2×2 + 右侧1个大格
- `fan_shaped`：扇形展开，上1中2下2

---

## 风格说明

### folder ⭐ 大爷最爱
**参考图**：`cover-image-styles/folder-reference.webp`  
**感觉**：拟物化写字板 + 3D微缩场景 + 模块化文件夹卡片  
**配色**：克莱因蓝(#0046D5) + 活力橙(#FF6B35)  
**适用**：投资机会、赛道机会、热点前瞻类封面

---

## 参考图目录

**完整中文索引**：`参考图目录.md`（收录97张参考图）

| 目录 | 图片数 | 用途 |
|------|--------|------|
| cover-image-styles/ | 13张 | 封面参考图 |
| article-illustrator-styles/ | 16张 | 文章插图 |
| infographic-styles/ | 37张 | 信息图 |
| slide-deck-styles/ | 14张 | PPT幻灯片 |
| xhs-images-styles/ | 17张 | 小红书风格 |

---

## 配置化说明

所有配置均可通过 `config/styles_config.yaml` 维护，无需改代码：

```yaml
# 赛道→风格映射
theme_styles:
  算力: "blueprint_lab"
  投资机会: "folder"
  ...

# 赛道→图标映射
stock_topic_slot_icons:
  AI数字经济: "电路板+芯片图标"
  ...

# 风格→参考图映射
style_ref_map:
  blueprint_lab: "blueprint.webp"
  folder: "folder-reference.webp"
  ...
```

---

## 输出目录

```
D:\AI_Workspace\reports\images\
└── *.png    # 封面图
```
