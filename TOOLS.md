# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## ⚠️ 搜索引擎配置（重要！）

**web_search 工具（Brave API）未配置 API Key，不可用。**

所有网页搜索必须通过 MCP：
```bash
# 主搜索引擎：MiniMax MCP
mcporter call MiniMax.web_search query="搜索关键词" --output json

# 备用搜索引擎：open-websearch (DuckDuckGo/Bing)
mcporter call open-websearch.search query="关键词" engine=bing --output json

# 备用搜索引擎：exa
mcporter call exa.web_search_exa query="关键词" --output json
```

调用方式：用 `exec` 工具执行上述命令，timeout 建议 30s。
可以并行调用多个搜索。

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
