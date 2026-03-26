---
name: imagen
description: |
  使用火山引擎的图像生成能力创建图片。
  当用户需要创建、生成或制作任何用途的图片时使用此技能，
  包括UI模型、图标、插图、图表、概念艺术、占位图片或视觉表现。
MANDATORY TRIGGERS: 生图, AI生图, 图像生成, 生成图片, 火山引擎, 豆包生图, 字节生图, text to image, generate image
---

# Imagen - AI图像生成技能

## 概述

本技能使用火山引擎的图像生成模型（doubao-seedream-5-0-260128）生成图片。它能在任何Claude Code会话中无缝生成图片——无论你是在构建前端UI、创建文档，还是需要概念的可视化表现。

**跨平台**：支持Windows、macOS和Linux。

## 何时使用此技能

当以下情况时自动激活此技能：
- 用户请求生成图片（例如："生成一张...的图片"、"创建一张图片"）
- 前端开发需要占位图或实际图片
- 文档需要插图或图表
- 可视化概念、架构或想法
- 创建图标、logo或UI素材
- 任何AI生成图片有帮助的任务

## 工作原理

1. 获取描述所需图片的文本提示词
2. 使用图像生成配置调用火山引擎API
3. 将生成的图片保存到指定位置（默认：`{WORKSPACE}\reports\images`）
4. 返回文件路径以便在项目中使用

## 使用方法

### Python（跨平台 - 推荐）

```bash
# 基本用法（默认保存到 {WORKSPACE}\reports\images）
python scripts/generate_image.py "未来城市天际线日落"

# 自定义输出路径
python scripts/generate_image.py "简约音乐播放器应用图标" "reports/images/music-icon.png"

# 自定义尺寸
python scripts/generate_image.py --size 1280x720 "高分辨率风景" "reports/images/wallpaper.png"
```

## 配置要求

- 必须设置 `ARK_API_KEY` 环境变量（已在openclaw.json中配置）
- Python 3.6+
- 需要安装openai库：`pip install openai`

## 默认设置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 分辨率 | 4K | 模型自动匹配尺寸 |
| 水印 | 无 | watermark=False |
| 格式 | PNG | output_format=png |

**提示**：在prompt中描述比例（如"9:16竖版"），模型会自动匹配对应尺寸

## 输出

生成的图片保存为PNG文件。脚本返回：
- 成功：生成的图片路径
- 失败：详细错误信息

## 文件输出目录

所有生成的图片默认保存到：
```
{WORKSPACE}\reports\images\
```

## 命令行参数


| 参数 | 说明 | 示例 |
|------|------|------|
| `prompt` | 提示词 | `"一只可爱的猫"` |
| `output` | 输出路径 | `images/cat.png` |
| `--size`, `-s` | 图片尺寸 | `4K`, `2K`, `1280x720` |
| `--model`, `-m` | 模型ID | `doubao-seedream-5-0-260128` |
| `--ref`, `-r` | 参考图片 | `--ref image1.png image2.png` |
| `--no-watermark` | 无水印 | `--no-watermark` |

### 图生图模式

```bash
# 单张参考图
python scripts/generate_image.py "将图片转为卡通风格" --ref original.png --output cartoon.png

# 多张参考图（最多4张）
python scripts/generate_image.py "结合图1的服装和图2的背景" --ref person.png scene.png --output result.png

# 指定模型（图生图需要5系模型）
python scripts/generate_image.py "参考这张图生成类似风格" --ref style.png --model doubao-seedream-5-0-260128 --output new.png
```

**注意**：图生图功能需要使用 `doubao-seedream-5-0-260128` 模型（4系模型不支持）

## 支持的分辨率

| 尺寸 | 说明 |
|------|------|
| 4K | 超高清（默认），模型自动匹配宽高比 |
| 3K | 高清 |
| 2K | 标准 |
| 1280x720 | 720p |
| 720x1280 | 竖版 |

**使用技巧**：在prompt中描述比例，如"9:16竖版，适合手机端展示"，模型会自动匹配
