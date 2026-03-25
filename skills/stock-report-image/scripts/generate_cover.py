# -*- coding: utf-8 -*-
"""
热点报告配图生成器 - 智能封面版
支持：--cover（1张整合封面，自动匹配多参考图）
"""
import sys
import os
import re
import io
import shutil
import yaml
from pathlib import Path

# 修复 Windows 控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from datetime import datetime

# ==================== 路径配置（动态适配OpenClaw工作目录）====================
# 自动计算路径，无需硬编码，适配任意工作目录
SCRIPT_DIR = Path(__file__).parent  # 脚本所在目录: /skills/stock-report-image/scripts
SKILL_ROOT = SCRIPT_DIR.parent      # 技能根目录: /skills/stock-report-image
SKILLS_DIR = SKILL_ROOT.parent      # 技能总目录: /skills
BASE_DIR = SKILLS_DIR.parent        # OpenClaw工作根目录（自动识别）

# 业务路径（自动适配当前工作目录）
REPORTS_DIR = BASE_DIR / "stock-analyst-cat" / "reports"  # A股报告目录
OUTPUT_DIR = BASE_DIR / "reports" / "images" / "stock-covers"  # 输出目录
CONFIG_DIR = SKILL_ROOT / "config"  # 配置文件目录
# 生图模型路径（自动检测可用）
IMAGEN_SCRIPT = SKILLS_DIR / "imagen" / "scripts" / "generate_image.py"  # 火山引擎imagen
AUTOGLM_SCRIPT = SKILLS_DIR / "autoglm-generate-image" / "generate-image.py"  # 智谱autoglm
DOCS_DIR = SKILL_ROOT / "docs"  # 本技能文档目录
REF_DIRS = [
    SKILL_ROOT / "cover-image-styles",
    SKILL_ROOT / "article-illustrator-styles",
    SKILL_ROOT / "infographic-reference",
    SKILL_ROOT / "xhs-images-styles",  # 保留小红书风格资源
    SKILL_ROOT / "xhs-images-layouts",  # 保留小红书布局资源
]


# ==================== 读取prompt模板文件 ====================
def load_prompt_template(template_name: str) -> str:
    """从docs目录读取prompt模板"""
    template_path = DOCS_DIR / template_name
    if template_path.exists():
        content = template_path.read_text(encoding='utf-8')
        # 提取英文部分（支持多种格式）
        if "## English" in content:
            # 格式1: ## English / ## 中文
            en_part = content.split("## English")[1].split("## 中文")[0] if "## 中文" in content else content.split("## English")[1]
            return en_part.strip()
        elif "# " in content and "===" not in content[:100]:
            # 格式2: 纯英文内容，无中英文分隔
            return content.strip()
        else:
            # 找不到英文部分，返回空
            return ""
    return ""


# 预加载常用模板
PROMPT_TEMPLATES = {
    "neg_constraints": load_prompt_template("negative-constraints.md"),
}

# ==================== 加载风格配置（优先读取config/styles_config.yaml，不存在则用默认值
CONFIG_PATH = CONFIG_DIR / "styles_config.yaml"
DEFAULT_STYLE_REF_MAP = {
    "blueprint_lab": "blueprint.webp",
    "retro_pop_grid": "retro.webp",
    "acid_block": "cyberpunk-neon.webp",
    "thermal": "chalkboard.webp",
    "vintage_journal": "vintage.webp",
    "folder": "flat.webp",
    "archive": "editorial.webp",
    "ticket": "playful.webp",
    "blueprint": "blueprint.webp",
    "retro": "retro.webp",
    "chalkboard": "chalkboard.webp",
    "vintage": "vintage.webp",
    "minimal": "flat.webp",
}
DEFAULT_THEME_STYLES = {
    "算力": "blueprint_lab", "芯片": "blueprint_lab", "AI": "blueprint_lab",
    "人工智能": "blueprint_lab", "半导体": "blueprint_lab",
    "电力": "blueprint_lab", "电网": "blueprint_lab", "变压器": "blueprint_lab",
    "光伏": "blueprint_lab", "新能源": "blueprint_lab",
    "航天": "blueprint_lab", "卫星": "blueprint_lab", "火箭": "blueprint_lab", "低空": "blueprint_lab",
    "钨": "retro_pop_grid", "稀土": "retro_pop_grid", "小金属": "retro_pop_grid",
    "黄金": "retro_pop_grid", "白银": "retro_pop_grid", "铜": "retro_pop_grid",
    "锂": "retro_pop_grid", "镍": "retro_pop_grid", "金属": "retro_pop_grid",
    "战略金属": "retro_pop_grid", "磷化工": "vintage_journal", "化肥": "vintage_journal",
    "化工": "vintage_journal", "医药": "vintage_journal", "医疗": "vintage_journal",
    "金融": "archive", "银行": "archive", "锂电": "acid_block", "电池": "acid_block",
}
DEFAULT_STYLE = "blueprint_lab"

# A股赛道→精确图标描述（大爷验证最优格式，逐格定义的关键配置）
DEFAULT_STOCK_TOPIC_SLOT_ICONS = {
    "AI数字经济": "电路板+芯片图标",
    "有色金属": "金矿+金属晶体图标",
    "储能锂电": "太阳能板+电池图标",
    "量子通信": "量子波动+盾牌图标",
    "深海科技": "海浪+潜水器图标",
    "投资机会": "上涨箭头+K线图",
    "博鳌论坛": "会议场馆+地球图标",
    "稀土": "稀土矿石+发光晶体图标",
    "黄金": "金块+金币图标",
    "铜": "铜块+电缆图标",
    "油气": "石油钻井+输油管道图标",
    "航运": "集装箱货轮+港口图标",
    "机器人": "人形机器人+机械臂图标",
    "算力": "GPU芯片+服务器图标",
    "芯片": "方形芯片+针脚图标",
    "航天": "火箭+卫星图标",
    "医药": "药瓶+分子结构图标",
    "光伏": "光伏板+阳光图标",
    "电网": "电塔+电网图标",
    "银行": "银行大楼+钱币图标",
    "战略金属": "金黄色金属矿石+钨矿图标",
    "小金属": "铜矿+锌矿+金属矿石图标",
    "电力": "电塔+变压器+电网图标",
    "特高压": "特高压电塔+输电线路图标",
}

# 加载配置文件
STYLE_REF_MAP = DEFAULT_STYLE_REF_MAP
THEME_STYLES = DEFAULT_THEME_STYLES
STOCK_TOPIC_SLOT_ICONS = DEFAULT_STOCK_TOPIC_SLOT_ICONS.copy()

if CONFIG_PATH.exists():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        if config.get("style_ref_map"):
            STYLE_REF_MAP.update(config["style_ref_map"])
        if config.get("theme_styles"):
            THEME_STYLES.update(config["theme_styles"])
        if config.get("default_style"):
            DEFAULT_STYLE = config["default_style"]
        if config.get("stock_topic_slot_icons"):
            STOCK_TOPIC_SLOT_ICONS.update(config["stock_topic_slot_icons"])
        print(f"[INFO] 已加载风格配置: {CONFIG_PATH}")
    except Exception as e:
        print(f"[WARN] 配置文件加载失败，使用默认配置: {e}")
else:
    # 配置文件不存在，自动生成默认配置
    default_config = {
        "style_ref_map": DEFAULT_STYLE_REF_MAP,
        "theme_styles": DEFAULT_THEME_STYLES,
        "default_style": DEFAULT_STYLE
    }
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
        print(f"[INFO] 已生成默认配置文件: {CONFIG_PATH}")
    except Exception as e:
        print(f"[WARN] 生成配置文件失败: {e}")



def find_ref_image(style_key: str) -> Path:
    """根据风格找到参考图路径"""
    ref_filename = STYLE_REF_MAP.get(style_key, "blueprint.webp")
    
    for ref_dir in REF_DIRS:
        ref_path = ref_dir / ref_filename
        if ref_path.exists():
            return ref_path
    
    return None


def detect_style_for_topic(topic: str) -> str:
    """根据主题关键字判断风格"""
    # 检查主题中是否包含关键词
    for keyword, style in THEME_STYLES.items():
        if keyword in topic:
            return style
    return DEFAULT_STYLE


def analyze_topics_for_cover(topics: list) -> dict:
    """
    智能分析多主题，返回封面生成参数
    返回: {
        "styles": [{"topic": "电网", "style": "blueprint_lab", "ref": Path}],
        "merged_topics": ["电网", "光伏", "火箭", "小金属"],
        "dominant_style": "blueprint_lab",
        "ref_images": [Path1, Path2, ...]
    }
    """
    style_counts = {}
    style_refs = {}
    topic_styles = []
    
    print(f"\n[智能分析] 主题数量: {len(topics)}")
    
    # 1. 为每个主题判断风格
    for topic in topics:
        style = detect_style_for_topic(topic)
        ref_path = find_ref_image(style)
        
        topic_styles.append({
            "topic": topic,
            "style": style,
            "ref": ref_path
        })
        
        # 统计风格出现次数
        if style not in style_counts:
            style_counts[style] = 0
            style_refs[style] = ref_path
        style_counts[style] += 1
        
        print(f"  - {topic} → {style}")
    
    # 2. 找出多数风格
    dominant_style = max(style_counts, key=style_counts.get)
    
    # 3. 收集所有参考图（去重）
    ref_images = []
    seen = set()
    for ts in topic_styles:
        if ts["ref"] and ts["ref"] not in seen:
            ref_images.append(ts["ref"])
            seen.add(ts["ref"])
    
    print(f"\n[风格统计]")
    for style, count in style_counts.items():
        print(f"  - {style}: {count}个主题")
    print(f"[参考图] {len(ref_images)}张")
    
    return {
        "topic_styles": topic_styles,
        "merged_topics": topics,
        "dominant_style": dominant_style,
        "ref_images": ref_images,
    }


def build_cover_prompt(analysis: dict, args=None) -> dict:
    """为封面图生成提示词（支持多参考图）- 优化版
    args: 命令行参数，支持layout/style/platform覆盖
    """
    topics = analysis["merged_topics"]
    style = analysis["dominant_style"]
    ref_images = analysis["ref_images"]
    
    # 1. 构建主题描述 - 用逗号分隔，更清晰
    topics_text = "、".join(topics)
    
    # 2. 【核心优化】逐格精确定义（大爷验证最优格式）
    # 用STOCK_TOPIC_SLOT_ICONS查图标，没有的话用"科技图表"兜底
    def get_topic_icon(topic):
        for kw, icon in STOCK_TOPIC_SLOT_ICONS.items():
            if kw in topic:
                return icon
        return "科技图表"

    # 用户指定布局优先，否则根据主题数量自动适配
    custom_layout = getattr(args, "layout", None) if args else None
    if custom_layout:
        # 用户指定了布局
        layout_type = custom_layout
        print(f"[INFO] 已使用指定布局：{custom_layout}")
    elif topic_count == 1:
        layout_type = "single"
    elif topic_count == 2:
        layout_type = "two_column"
    elif topic_count == 3:
        layout_type = "three_column"
    elif topic_count == 4:
        layout_type = "grid_2x2"
    elif topic_count == 5:
        layout_type = "hub_spoke"
    elif topic_count == 6:
        layout_type = "grid_2x3"
    else:
        layout_type = "single"

    # 构建逐格描述（大爷验证最优格式）
    slot_lines = []
    if layout_type == "grid_2x3":
        # 2x3六宫格：上左/上中/上右/下左/下中/下右
        positions = ["上左格", "上中格", "上右格", "下左格", "下中格", "下右格"]
        for i, topic in enumerate(topics[:6]):
            icon = get_topic_icon(topic)
            slot_lines.append(f"{i+1}. {positions[i]}：{icon}，标注'{topic}'")
    elif layout_type == "hub_spoke":
        # 环形放射：5个面板围绕中心标题
        positions = ["左上方（约11点方向）", "右上方（约1点方向）",
                    "正左侧（约9点方向）", "正右侧（约3点方向）", "正下方（约6点方向）"]
        for i, topic in enumerate(topics[:5]):
            icon = get_topic_icon(topic)
            slot_lines.append(f"- {positions[i]}：{icon}，标注'{topic}'")
        topic_visual_text = "\n".join(slot_lines)
        topic_visual_text = "5个面板围绕中心标题：\n" + topic_visual_text
    elif layout_type == "fan_shaped":
        # 扇形展开：上1中2下2，像扇子一样打开
        positions = [
            "顶部中央（扇形顶点）",
            "中左（扇骨左侧）",
            "中右（扇骨右侧）",
            "底左（扇骨左下）",
            "底右（扇骨右下）",
        ]
        for i, topic in enumerate(topics[:5]):
            icon = get_topic_icon(topic)
            slot_lines.append(f"{i+1}. {positions[i]}：{icon}，标注'{topic}'")
        topic_visual_text = "\n".join(slot_lines)
        topic_visual_text = "扇形展开布局，5个面板呈放射状：\n" + topic_visual_text
    elif layout_type == "left4_right1":
        # 左侧4格2x2 + 右侧1个大格
        positions = ["左上格", "右上格", "左下格", "右下格"]
        for i, topic in enumerate(topics[:4]):
            icon = get_topic_icon(topic)
            slot_lines.append(f"{i+1}. {positions[i]}：{icon}，标注'{topic}'")
        slot_lines.append(f"5. 右侧大格（突出总结区）：{get_topic_icon(topics[4] if len(topics)>4 else topics[-1])}，标注'{topics[4] if len(topics)>4 else topics[-1]}'")
        topic_visual_text = "\n".join(slot_lines)
        topic_visual_text = "左侧4格2x2网格 + 右侧1个大格：\n" + topic_visual_text
    elif layout_type == "top3_bottom2":
        # 顶部3格横排 + 底部2格横排
        positions = ["上左格", "上中格", "上右格", "下左格", "下右格"]
        for i, topic in enumerate(topics[:5]):
            icon = get_topic_icon(topic)
            slot_lines.append(f"{i+1}. {positions[i]}：{icon}，标注'{topic}'")
        topic_visual_text = "\n".join(slot_lines)
        topic_visual_text = "顶部3格横排 + 底部2格横排：\n" + topic_visual_text
    elif layout_type == "grid_2x2":
        positions = ["左上格", "右上格", "左下格", "右下格"]
        for i, topic in enumerate(topics[:4]):
            icon = get_topic_icon(topic)
            slot_lines.append(f"{i+1}. {positions[i]}：{icon}，标注'{topic}'")
    elif layout_type == "three_column":
        positions = ["左格", "中格", "右格"]
        for i, topic in enumerate(topics[:3]):
            icon = get_topic_icon(topic)
            slot_lines.append(f"{i+1}. {positions[i]}：{icon}，标注'{topic}'")
    elif layout_type == "two_column":
        positions = ["左格", "右格"]
        for i, topic in enumerate(topics[:2]):
            icon = get_topic_icon(topic)
            slot_lines.append(f"{i+1}. {positions[i]}：{icon}，标注'{topic}'")
    else:
        # 单面板
        topic_visual_text = f"1. 中央区域：{get_topic_icon(topics[0])}，标注'{topics[0]}'"

    if slot_lines:
        topic_visual_text = "\n".join(slot_lines)
    
    # 3. 构建参考图描述（关键！）
    ref_descriptions = []
    for i, ref_path in enumerate(ref_images, 1):
        ref_filename = ref_path.name
        style_name = ref_path.stem
        
        ref_desc = f"""
## 参考图{i} ({ref_filename}):
- 风格: {style_name}
- 必须严格遵循此参考图的：
  * 配色方案（主色、辅色、强调色）
  * 渲染风格（线条、纹理、深度）
  * 视觉元素（图标、装饰）
- 生成的图片必须看起来与参考图属于同一视觉系列"""
        ref_descriptions.append(ref_desc)
    
    # 4. 英文提示词 - 只保留负向约束（其他模板已删除）
    templates = []
    if PROMPT_TEMPLATES.get("neg_constraints"):
        templates.append(f"=== NEGATIVE CONSTRAINTS (from baoyu-skills) ===\n{PROMPT_TEMPLATES['neg_constraints']}")
    
    template_text = "\n\n".join(templates)
    
    # 平台适配：获取对应比例（必须在en_prompt之前，因为f-string里用了aspect_ratio）
    platform = getattr(args, "platform", "toutiao") if args else "toutiao"
    aspect_ratio = config.get("platform_aspect_ratios", {}).get(platform, "16:9")
    print(f"[INFO] 适配平台：{platform}，使用比例：{aspect_ratio}")
    
    en_prompt = f"""Create a professional financial news cover image.

=== COVER TEXT (MUST DISPLAY CLEARLY) ===
Title: "A股热点前瞻"
Subtitle: "{topics_text}"

=== TOPIC VISUALS (Each topic must have corresponding visual) ===
{topic_visual_text}

{template_text}

=== LAYOUT REQUIREMENTS ===
- Title text at top: "A股热点前瞻" - large, bold
- Subtitle: "{topics_text}" - clearly readable
- 【关键】严格按照以下逐格描述生成，每个格子位置和内容都必须精确对应：
{topic_visual_text}
- 每个面板必须有清晰边框包裹
- 色调统一，整体偏暖色系或科技蓝色系
- 专业金融研报质感，无人物，高质量

=== STYLE REQUIREMENTS (MUST FOLLOW REFERENCES) ===
{''.join(ref_descriptions)}

=== TECHNICAL ===
- Aspect ratio: {aspect_ratio}
- High quality 4K
- Financial news media style
- Clean, professional layout""".format(aspect_ratio=aspect_ratio)
    
    # 5. 中文提示词（大爷验证最优格式，逐格精确定义，全中文避免乱码）
    
    # 风格映射：style_key → 中文背景风格描述
    style_bg_map = {
        "folder": "拟物化文件夹/写字板质感背景",
        "blueprint_lab": "科技蓝图风格背景",
        "retro_pop_grid": "复古波普网格风格背景",
        "acid_block": "赛博朋克霓虹风格背景",
        "thermal": "手绘黑板风格背景",
        "vintage_journal": "复古期刊风格背景",
        "archive": "档案文件风格背景",
        "ticket": "票据风格背景",
    }
    bg_style = style_bg_map.get(style, "专业金融研报风格背景")
    
    # 主标题
    main_title = "A股热点前瞻"
    if topics_text:
        main_title_candidates = [t for t in topics if any(kw in t for kw in ["机会", "赛道", "前瞻", "热点"])]
        if main_title_candidates:
            main_title = f"A股{''.join(main_title_candidates[:2])}"
    
    # 布局描述
    if layout_type == "grid_2x3":
        layout_desc = "2x3网格布局"
    elif layout_type == "hub_spoke":
        layout_desc = "环形放射布局"
    elif layout_type == "grid_2x2":
        layout_desc = "2x2网格布局"
    elif layout_type == "three_column":
        layout_desc = "左中右三栏布局"
    else:
        layout_desc = "网格布局"
    
    # 面板边框要求
    border_req = "每个板块有清晰边框和背景纹理"
    
    # 面板逐格描述（已有topic_visual_text）
    slots_text = topic_visual_text.replace("\n", "\n")
    
    cn_prompt = f"""{aspect_ratio}宽屏比例，{bg_style}，寻找A股投资机会主题。采用{layout_desc}，{border_req}：
{slots_text}
顶部居中大标题：'{main_title}'，字体稳重清晰，整体色调统一偏暖色系，专业金融研报质感，无人物，高质量，无文字错误

=== 负向约束（禁止事项）===
- 禁止水印、禁止平台标签、禁止来源标注
- 禁止边框缺失、禁止面板截断
- 禁止文字叠加、禁止标签栏出现非指定文字
- 禁止文字乱码、禁止笔画错误
""".format(aspect_ratio=aspect_ratio)

    return {
        "cn": cn_prompt,
        "en": en_prompt,
        "topics": topics_text,
        "style": style,
        "ref_images": ref_images,
        "ref_params": [],  # 用于imagen调用
    }


def extract_topics_from_report(report_path: Path) -> list:
    """从报告中提取热点主题 - 优化版"""
    for encoding in ["utf-8", "utf-8-sig", "gbk", "gb2312"]:
        try:
            content = report_path.read_text(encoding=encoding)
            break
        except:
            continue
    
    topics = []
    
    # 匹配模式：优先提取带emoji的完整主题行
    patterns = [
        # 匹配 "💎 主题：【算力自主】【业绩驱动】【🟡中风险】" 格式
        r'💎 主题：【(.+?)】',
        # 匹配 "主题：【算力自主】+【业绩驱动】" 格式
        r'主题：【(.+?)】',
        # 匹配 "【算力自主】+【业绩驱动】" 格式
        r'【(.+?)】\+【(.+?)】',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content)
        if matches:
            for m in matches:
                if isinstance(m, tuple):
                    # 合并多标签，但只取第一个核心词
                    # "算力自主" + "业绩驱动" → "算力自主"（取第一个）
                    core_topic = m[0].strip() if m[0].strip() else m[1].strip()
                else:
                    # 处理 "算力自主 + 业绩驱动" 格式
                    # 分割+号，取第一个核心词
                    topic = m.strip()
                    if '+' in topic:
                        parts = topic.split('+')
                        core_topic = parts[0].strip()
                    else:
                        core_topic = topic
                
                if core_topic and core_topic not in topics:
                    topics.append(core_topic)
            if topics:
                break
    
    # 备用：如果没找到，尝试提取第一行 ## 标题作为主题
    if not topics:
        lines = content.split('\n')
        for line in lines:
            # 匹配 "## 🔥 热点一：xxx" 格式
            match = re.search(r'## .? .+?：(.+)', line)
            if match:
                topic = match.group(1).strip()
                if topic and len(topic) < 20:  # 过滤太长的
                    topics.append(topic)
    
    return topics


def find_latest_report() -> Path:
    """找到最新的报告"""
    reports = sorted(REPORTS_DIR.glob("*.md"), key=os.path.getmtime, reverse=True)
    return reports[0] if reports else None


def copy_refs_to_output(ref_images: list, output_dir: Path) -> list:
    """复制参考图到输出目录的refs子目录"""
    refs_dir = output_dir / "refs"
    refs_dir.mkdir(parents=True, exist_ok=True)
    
    copied_paths = []
    for ref_path in ref_images:
        dest = refs_dir / ref_path.name
        shutil.copy2(ref_path, dest)
        copied_paths.append(dest)
        print(f"  [复制参考图] {ref_path.name} → refs/")
    
    return copied_paths


def generate_image(prompt: str, output_path: Path, ref_images: list = None, model: str = "imagen") -> bool:
    """调用生图模型生成图片，支持imagen和autoglm"""
    import subprocess
    import json
    
    if model == "imagen" and not IMAGEN_SCRIPT.exists():
        print(f"[IMAGEN] ❌ imagen脚本不存在，自动切换到autoglm")
        model = "autoglm"
    if model == "autoglm" and not AUTOGLM_SCRIPT.exists():
        print(f"[AUTOGLM] ❌ autoglm脚本不存在")
        return False
    
    try:
        if model == "imagen":
            # 火山引擎imagen调用格式：python generate_image.py prompt output_path --ref ref1 --ref ref2
            cmd = [
                sys.executable,
                str(IMAGEN_SCRIPT),
                prompt,
                str(output_path),
            ]
            if ref_images:
                for ref in ref_images:
                    cmd.extend(["--ref", str(ref)])
            print(f"[IMAGEN] 正在生成图片...")
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
            
        elif model == "autoglm":
            # 智谱autoglm调用格式：python generate-image.py "prompt"
            cmd = [
                sys.executable,
                str(AUTOGLM_SCRIPT),
                prompt,
            ]
            print(f"[AUTOGLM] 正在生成图片...")
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
            
            # 处理autoglm返回结果，保存图片到指定路径
            if result.returncode == 0:
                try:
                    # 解析返回的json，提取image_url
                    resp = json.loads(result.stdout.strip())
                    if resp.get("code") == 0 and resp.get("data", {}).get("image_url"):
                        import requests
                        img_url = resp["data"]["image_url"]
                        # 下载图片到指定路径
                        img_resp = requests.get(img_url, timeout=30)
                        if img_resp.status_code == 200:
                            with open(output_path, "wb") as f:
                                f.write(img_resp.content)
                            print(f"[AUTOGLM] ✅ 图片下载完成: {output_path.name}")
                            return True
                        else:
                            print(f"[AUTOGLM] ❌ 图片下载失败: {img_resp.status_code}")
                            return False
                except Exception as e:
                    print(f"[AUTOGLM] ❌ 结果解析失败: {e}，返回内容：{result.stdout[:200]}")
                    return False
    
        # 统一结果处理
        if result.returncode == 0:
            print(f"[{model.upper()}] ✅ 生成成功: {output_path.name}")
            return True
        else:
            print(f"[{model.upper()}] ❌ 生成失败: {result.stderr[:200]}")
            # 失败时保存提示词到本地，方便手动调用
            prompt_save_path = output_path.with_suffix(".prompt.txt")
            prompt_save_path.write_text(prompt, encoding="utf-8")
            print(f"💡 提示词已保存到: {prompt_save_path}，可手动调用生图")
            return False
            
    except Exception as e:
        print(f"[{model.upper()}] ❌ 调用失败: {e}")
        # 失败时保存提示词
        prompt_save_path = output_path.with_suffix(".prompt.txt")
        prompt_save_path.write_text(prompt, encoding="utf-8")
        print(f"💡 提示词已保存到: {prompt_save_path}")
        return False


def main():
    import argparse
    
    # 前置检查：生图模型可用性
    AVAILABLE_MODELS = []
    if IMAGEN_SCRIPT.exists():
        AVAILABLE_MODELS.append("imagen")
    if AUTOGLM_SCRIPT.exists():
        AVAILABLE_MODELS.append("autoglm")
    
    if not AVAILABLE_MODELS and not args.prompt_only:
        print("❌ 依赖缺失：未找到任何可用的生图模型！")
        print(f"👉 请先安装以下任意一个技能：")
        print(f"   - imagen: {SKILLS_DIR / 'imagen'}")
        print(f"   - autoglm-generate-image: {SKILLS_DIR / 'autoglm-generate-image'}")
        print("💡 若仅需要生成提示词，可添加 --prompt-only 参数跳过生图步骤")
        return
    
    # 自动选择优先模型（优先用imagen，没有的话用autoglm）
    DEFAULT_MODEL = AVAILABLE_MODELS[0] if AVAILABLE_MODELS else None
    print(f"[INFO] 可用生图模型：{AVAILABLE_MODELS}，默认使用：{DEFAULT_MODEL}")
    
    parser = argparse.ArgumentParser(description="热点报告智能封面生成器")
    parser.add_argument("--model", type=str, choices=["imagen", "autoglm"], default=DEFAULT_MODEL, help="指定生图模型（默认自动选择）")
    # 新增进阶参数，可选，不指定则自动适配
    parser.add_argument("--layout", type=str, help="指定布局（可选：single_panel/two_column/three_column/grid_2x2/pyramid/journey_path/timeline_horizontal/mind_map/venn/funnel等20种）")
    parser.add_argument("--style", type=str, help="指定风格（可选：blueprint_lab/retro_pop_grid/vintage_journal/acid_block/playful/retro/watercolor等17种）")
    parser.add_argument("--platform", type=str, choices=["toutiao", "xhs", "wechat"], default="toutiao", help="适配平台（默认toutiao，可选xhs/wechat）")
    parser.add_argument("--report", type=str, default="latest", help="报告文件名")
    parser.add_argument("--cover", action="store_true", help="生成封面图（1张整合所有主题）")
    parser.add_argument("--illustrate", action="store_true", help="为每个主题生成配图")
    parser.add_argument("--prompt-only", action="store_true", help="仅生成提示词")
    parser.add_argument("--auto", "-a", action="store_true", help="自动模式：读取报告→智能分析→生成封面")
    
    args = parser.parse_args()
    
    # 1. 找到报告
    if args.report == "latest":
        report_path = find_latest_report()
    else:
        report_path = REPORTS_DIR / args.report
    
    if not report_path or not report_path.exists():
        print(f"Error: 报告未找到: {args.report}")
        return
    
    print(f"[INFO] 读取报告: {report_path.name}")
    
    # 2. 提取主题
    topics = extract_topics_from_report(report_path)
    
    if not topics:
        print("⚠️  未自动识别到热点主题，请手动输入主题（多个用空格分隔）：")
        user_input = input("> ").strip()
        if not user_input:
            print("❌ 未输入主题，退出")
            return
        topics = [t.strip() for t in user_input.split() if t.strip()]
    
    # 主题太少时，询问是否补充
    elif len(topics) < 2:
        print(f"⚠️  仅识别到 {len(topics)} 个主题: {topics}")
        print("是否需要补充其他主题？直接输入补充的主题（多个用空格分隔），按回车跳过：")
        user_input = input("> ").strip()
        if user_input:
            extra_topics = [t.strip() for t in user_input.split() if t.strip()]
            topics.extend(extra_topics)
    
    print(f"[INFO] 最终主题列表: {topics}")
    
    # 3. 智能分析（--cover 模式）
    if args.cover or args.auto:
        print(f"\n[封面模式] 智能分析多主题...")
        
        analysis = analyze_topics_for_cover(topics)
        
        # 强制覆盖用户指定的风格
        if args.style:
            if args.style in STYLE_REF_MAP:
                analysis["dominant_style"] = args.style
                print(f"[INFO] 已强制使用指定风格：{args.style}")
            else:
                print(f"[WARN] 未知风格：{args.style}，将使用自动匹配的风格：{analysis['dominant_style']}")
        
        # 构建封面提示词，传入用户参数
        prompt_data = build_cover_prompt(analysis, args=args)
        
        print(f"\n{'='*60}")
        print(f"【封面提示词】")
        print(f"主题: {prompt_data['topics']}")
        print(f"风格: {prompt_data['style']}")
        print(f"参考图: {len(prompt_data['ref_images'])}张")
        print(f"{'='*60}")
        print(f"\n【英文提示词】\n{prompt_data['en']}")
        print(f"\n{'='*60}")
        
        if args.prompt_only:
            print("[INFO] 仅生成提示词模式")
            return
        
        # 4. 生成图片
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # 按日期创建子目录
        date_str = datetime.now().strftime("%Y-%m-%d")
        dated_output_dir = OUTPUT_DIR / date_str
        dated_output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%H%M%S")
        safe_topics = re.sub(r'[\\/:*?"<>|]', '_', topics[0])[:15]
        output_path = dated_output_dir / f"{timestamp}_cover_{safe_topics}.png"
        
        # 复制参考图到输出目录
        copied_refs = copy_refs_to_output(prompt_data["ref_images"], OUTPUT_DIR)
        
        print(f"\n[生成封面] 调用{args.model}模型...")
        success = generate_image(prompt_data["en"], output_path, copied_refs, model=args.model)
        
        if success:
            print(f"\n✅ 封面生成完成!")
            print(f"📁 保存位置: {output_path}")
        else:
            print(f"\n❌ 生成失败")
    
    # 4. 配图模式（每个主题单独一张）
    elif args.illustrate:
        print(f"\n[配图模式] 为每个主题生成单独配图...")
        
        for topic in topics:
            style = detect_style_for_topic(topic)
            ref_path = find_ref_image(style)
            
            print(f"\n[处理] {topic} → {style}")
            
            # 构建提示词
            en_prompt = f"""Create an illustration about「{topic}」. Style: {style}, 16:9, high quality 4K."""
            
            if ref_path:
                print(f"  [参考图] {ref_path.name}")
            
            if args.prompt_only:
                continue
            
            # 生成
            date_str = datetime.now().strftime("%Y-%m-%d")
            dated_output_dir = OUTPUT_DIR / date_str
            dated_output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%H%M%S")
            safe_topic = re.sub(r'[\\/:*?"<>|]', '_', topic)[:15]
            output_path = dated_output_dir / f"{timestamp}_{safe_topic}.png"
            
            refs = [ref_path] if ref_path else []
            generate_image(en_prompt, output_path, refs, model=args.model)
        
        print(f"\n✅ 配图生成完成!")


if __name__ == "__main__":
    main()
