# 阶段2：方案A技术研究报告

> 研究Claude Code Agent调度能力、MCP工具调用机制、子agent通信协议
> 版本：1.0 (2026-03-14)

---

## 研究1: Claude Code Agent工具能力

### 核心发现

Claude Code 有两种Agent机制：

1. **Skill系统** - 基于SKILL.md的轻量级任务定义
2. **Agent工具** - 基于agents/*.md的完整子代理

### Agent文件格式

```markdown
---
name: agent-name
description: Use this agent when...
model: inherit
color: blue
---

You are an expert...
```

### Agent调用方式

```markdown
## 使用Agent工具

当需要调用子代理时：
1. 使用Agent工具创建/调用agent
2. 传递任务上下文
3. 接收返回结果
4. 继续主流程
```

### 关键能力

| 能力 | 支持 | 说明 |
|------|------|------|
| 创建临时agent | ✅ | 通过Agent工具 |
| 任务委派 | ✅ | 支持subagent |
| 上下文传递 | ⚠️ | 需要显式传递 |
| 并行调用 | ✅ | 可同时创建多个 |
| 状态管理 | ⚠️ | 需自己维护 |

---

## 研究2: MCP工具调用机制

### 当前可用MCP服务器

| 服务器 | 工具数 | 用途 |
|--------|--------|------|
| MiniMax | 2 | 搜索 |
| exa | 2 | 搜索 |
| bochaWebSearch | 1 | 搜索 |
| aliyunWebSearch | 1 | 搜索 |
| context7 | 2 | 文档 |
| tavily | 5 | 搜索 |
| open-webSearch | 6 | 搜索 |
| playwright | 22 | 浏览器 |
| serena | 21 | 工具 |

### MCP调用示例

```python
# 搜索调用
mcporter call MiniMax.web_search query="关键词" freshness=pm

# 浏览器调用
mcporter call playwright...
```

### 特点

- 同步调用：等待返回
- 超时控制：30秒/服务器
- 错误处理：需要自己捕获

---

## 研究3: 子agent通信协议

### 当前架构问题

1. **上下文隔离**：每个agent独立上下文
2. **结果传递**：需要手动提取和传递
3. **状态管理**：主agent维护全局状态

### 通信模式

```
主Agent (stock-editor)
    ↓ 创建
子Agent1 (stock-analyst)
    ↓ 返回JSON
主Agent
    ↓ 创建
子Agent2 (stock-reviewer)
    ↓ 返回JSON
主Agent
    ↓ 汇总
最终输出
```

### 需要的协议设计

```json
{
  "protocol": "stock-analyst-cat-v1",
  "steps": [
    {
      "name": "analyze",
      "agent": "stock-analyst",
      "input": {...},
      "output": {...}
    },
    {
      "name": "review",
      "agent": "stock-reviewer",
      "input": {...},
      "output": {...}
    }
  ]
}
```

---

## 技术可行性评估

### Agent调度

| 维度 | 评估 | 备注 |
|------|------|------|
| 可行性 | ✅ 高 | Agent工具可用 |
| 复杂度 | ⚠️ 中 | 需要设计通信协议 |
| 可靠性 | ⚠️ 中 | 上下文传递需处理 |
| 性能 | ⚠️ 中 | 可能有延迟 |

### MCP调用

| 维度 | 评估 | 备注 |
|------|------|------|
| 可行性 | ✅ 高 | 已正常使用 |
| 集成度 | ⚠️ 中 | 需封装调用 |
| 扩展性 | ✅ 高 | 可添加新服务器 |

### 通信协议

| 维度 | 评估 | 备注 |
|------|------|------|
| 可行性 | ⚠️ 中 | 需全新设计 |
| 复杂度 | ⚠️ 高 | 多agent协调难 |
| 维护性 | ⚠️ 中 | 协议需迭代 |

---

## 替代方案

### 方案A1: 伪Agent调度（当前推荐）

不使用真正的Agent工具，而是：
1. 定义标准JSON格式
2. 模拟agent调用（人工切换）
3. 维护状态文件

**优点**：简单可靠
**缺点**：不真正自动化

### 方案A2: 完整Agent实现

使用Agent工具创建：
1. stock-analyst-agent
2. stock-reviewer-agent

**优点**：真正自动化
**缺点**：技术挑战大

### 方案A3: 混合模式

1. 简单任务用Agent
2. 复杂任务用Skill

**优点**：平衡效率
**缺点**：架构复杂

---

## 下一步建议

### 短期（1周）

- [ ] 尝试创建stock-analyst子agent
- [ ] 测试上下文传递
- [ ] 验证JSON通信格式

### 中期（2周）

- [ ] 实现伪Agent调度
- [ ] 积累调用经验
- [ ] 评估可靠性

### 长期（4周）

- [ ] 实现完整Agent调度
- [ ] 自动化评分
- [ ] 端到端测试

---

## 结论

| 方案 | 推荐度 | 理由 |
|------|--------|------|
| 方案A1 | ⭐⭐⭐⭐⭐ | 简单可靠，立即可做 |
| 方案A2 | ⭐⭐⭐ | 理想但风险高 |
| 方案A3 | ⭐⭐⭐⭐ | 平衡方案 |

**建议**：先方案A1，积累经验后方案A3
