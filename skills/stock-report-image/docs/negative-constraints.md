# Negative Constraints | 负向约束清单

> 来源：baoyu-skills/baoyu-cover-image/references/
> 用途：告诉AI「不能做什么」，比正面描述更有效

---

## English

### Why Negative Constraints Work Better

Positive prompts tell AI what TO do. Negative constraints tell AI what NOT to do.
Negative constraints are more precise because:
- "对称" can be interpreted in many ways
- "NOT asymmetric" is unambiguous
- AI tends to "hallucinate" extra elements → explicit bans prevent this

### Core Negative Constraints

```
=== NEGATIVE CONSTRAINTS (MUST NOT DO) ===

1. NO WATERMARKS & TAGS
   - NO watermarks of any kind
   - NO platform labels (微信公众号封面/抖音/小红书标签等)
   - NO source attribution text
   - NO "本文首发于xxx" type text

2. NO MISSING ELEMENTS
   - Every topic panel MUST have a visible border/frame
   - No panel may be left "unframed" or "borderless"
   - Each topic icon MUST be fully contained within its frame

3. NO EXTRA TEXT
   - Text is limited ONLY to: main title + topic labels
   - NO decorative text, NO annotations, NO explanatory notes
   - NO text overlaid on other text

4. NO LAYOUT DEVIATION
   - All panels must be equal in size
   - Equal spacing between panels
   - Center point to each panel: equal distance
   - NO tilted, shifted, or off-center panels

5. NO TEXT ERRORS
   - All Chinese characters must be correctly formed
   - NO character corruption, NO missing radicals, NO wrong components
   - If Chinese text is required: double-check stroke accuracy
```

---

## 中文

### 为什么负向约束比正向更有效

正向提示词告诉AI「要做什么」，负向约束告诉AI「不能做什么」。
负向约束更精确，因为：
- 「对称」可以有无数种理解
- 「不能不对称」没有歧义
- AI容易「幻觉」出额外元素 → 明确禁止可以防止这一点

### 核心负向约束

```
=== 负向约束（禁止事项）===

1. 禁止水印和标签
   - 禁止任何水印
   - 禁止平台标签（微信公众号封面/抖音/小红书等）
   - 禁止来源标注文字
   - 禁止"本文首发于xxx"类文字

2. 禁止元素缺失
   - 每个主题面板必须有可见的边框/框架
   - 禁止任何面板缺少边框
   - 每个主题图标必须完整包含在其框架内

3. 禁止额外文字
   - 文字仅限于：主标题 + 主题标签
   - 禁止装饰性文字、禁止注释、禁止说明文字
   - 禁止文字叠加在其他文字上

4. 禁止布局偏移
   - 所有面板尺寸必须相等
   - 面板间距必须相等
   - 中心点到每个面板的距离必须相等
   - 禁止倾斜、偏移、居中不准确的面板

5. 禁止文字错误
   - 所有中文字符必须正确完整
   - 禁止字符残缺、偏旁错误、笔画错误
   - 如需生成中文：仔细检查笔画准确性
```

---

## Application | 应用方式

When building prompts, insert at the end of the prompt:

```
[Negative Constraints from baoyu-skills]
```

The script automatically appends this reference to all cover generation prompts.
