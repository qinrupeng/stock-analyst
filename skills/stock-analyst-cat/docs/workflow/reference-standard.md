# 文档引用规范

> 如何在分析中引用三个模块的文档
> 版本：1.0 (2026-03-14)

---

## 引用原则

1. **必读文件**：每次分析必须读取的文件
2. **按需引用**：根据场景选择性读取
3. **引用标注**：在分析中标注参考了哪个文档

---

## 必读文件（每次分析）

| 优先级 | 文件 | 说明 |
|--------|------|------|
| 🔴 必须 | stock-editor/SKILL.md | 主编入口 |
| 🔴 必须 | stock-analyst/SKILL.md | 分析入口 |
| 🔴 必须 | stock-reviewer/SKILL.md | 审查入口 |

---

## 按需引用文件

### 场景解析时

```
引用: stock-editor/references/01-scenes.md
内容: 场景类型定义、关键词匹配规则
```

### 分析维度时

```
引用: stock-analyst/references/01-analysis.md
内容: 多维分析方法、驱动类型分类
```

### 态势评级时

```
引用: stock-analyst/references/02-rating.md
内容: 评分公式、评级标准、加减分规则
```

### 质量审查时

```
引用: stock-reviewer/references/02-checklist.md
内容: 7大检查项、质量分计算
```

---

## 引用格式

在分析报告中标注参考来源：

```markdown
**参考文档**:
- 主编: stock-editor/SKILL.md
- 分析: stock-analyst/SKILL.md + references/02-rating.md
- 审查: stock-reviewer/SKILL.md + references/02-checklist.md
```

---

## 引用检查清单

开始分析前确认：

- [ ] 已加载 stock-editor/SKILL.md
- [ ] 已加载 stock-analyst/SKILL.md
- [ ] 已加载 stock-reviewer/SKILL.md
- [ ] 已根据场景加载对应references

---

## 文档位置速查

```
stock-analyst-cat/
├── stock-editor/
│   ├── SKILL.md                    # 主编入口
│   └── references/
│       └── 01-scenes.md             # 场景定义
├── stock-analyst/
│   ├── SKILL.md                    # 分析入口
│   └── references/
│       ├── 01-analysis.md           # 分析方法
│       └── 02-rating.md            # 评级标准
├── stock-reviewer/
│   ├── SKILL.md                    # 审查入口
│   └── references/
│       ├── 01-quality.md            # 质量标准
│       └── 02-checklist.md         # 检查清单
└── docs/
    └── workflow/
        ├── operation-guide.md       # 操作指南
        └── reference-standard.md    # 本文档
```

---

## 更新同步规则

当更新任一模块的SKILL.md时：

1. 检查是否有对应的references需要更新
2. 更新本文档的引用说明
3. 记录变更到各模块的self-improving.md
