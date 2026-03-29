# -*- coding: utf-8 -*-
"""热点报告配图生成器 - yaml驱动版
所有布局位置、风格背景、提示词模板全部在yaml里
代码只做：读yaml → 读报告 → 组装 → 生图
"""
import sys, os, re, io, shutil, yaml
from pathlib import Path

# 修复 Windows 控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from datetime import datetime

# ==================== 路径配置 ====================
SCRIPT_DIR = Path(__file__).parent
SKILL_ROOT = SCRIPT_DIR.parent
SKILLS_DIR = SKILL_ROOT.parent
BASE_DIR = SKILLS_DIR.parent

REPORTS_DIR = BASE_DIR / "reports" / "stock"
OUTPUT_DIR = BASE_DIR / "reports" / "images" / "stock-covers"
CONFIG_DIR = SKILL_ROOT / "config"
IMAGEN_SCRIPT = SKILLS_DIR / "imagen" / "scripts" / "generate_image.py"
AUTOGLM_SCRIPT = SKILLS_DIR / "autoglm-generate-image" / "generate-image.py"
DOCS_DIR = SKILL_ROOT / "docs"
REF_DIRS = [
    SKILL_ROOT / "cover-image-styles",
    SKILL_ROOT / "article-illustrator-styles",
    SKILL_ROOT / "infographic-styles",
    SKILL_ROOT / "xhs-images-styles",
]

# ==================== 配置加载（全部从yaml，不写硬编码）====================
CONFIG_PATH = CONFIG_DIR / "styles_config.yaml"
CONFIG = {}

def _load_config():
    global CONFIG
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                CONFIG = yaml.safe_load(f) or {}
            print(f"[INFO] 已加载配置: {CONFIG_PATH}")
        except Exception as e:
            print(f"[ERROR] 配置文件加载失败: {e}")
    else:
        print(f"[ERROR] 配置文件不存在: {CONFIG_PATH}")

_load_config()

# ==================== 配置读取辅助 ====================
def get_style_ref_map():
    return CONFIG.get("style_ref_map", {})

def get_theme_styles():
    return CONFIG.get("theme_styles", {})

def get_topic_icons():
    return CONFIG.get("stock_topic_slot_icons", {})

def get_layout_positions():
    return CONFIG.get("layout_positions", {})

def get_style_bg_map():
    return CONFIG.get("style_bg_map", {})

def get_layout_assembly():
    return CONFIG.get("layout_assembly", {})

def get_default_style():
    return CONFIG.get("default_style", "blueprint_lab")

def get_aspect_ratio(platform):
    return CONFIG.get("platform_aspect_ratios", {}).get(platform, "16:9")

def get_folder_style_desc():
    return CONFIG.get("folder_style_desc", "")

# ==================== 核心函数 ====================

def find_ref_image(style_key: str) -> Path:
    ref_map = get_style_ref_map()
    ref_filename = ref_map.get(style_key, "blueprint.webp")
    for ref_dir in REF_DIRS:
        ref_path = ref_dir / ref_filename
        if ref_path.exists():
            return ref_path
    return None

def detect_style_for_topic(topic: str, full_content: str = "") -> tuple:
    """topic=主题标题, full_content=完整内容(含描述)，返回(style, matched_keyword)"""
    theme_styles = get_theme_styles()
    icons = get_topic_icons()
    default = get_default_style()
    scan_text = full_content if full_content else topic
    # 直接匹配：theme_styles的key是否在topic标题里
    for keyword, style in theme_styles.items():
        if keyword in topic:
            return style, keyword
    # 回退1：在完整内容中扫描fallback关键词
    fallback_map = CONFIG.get("theme_topic_fallback", {})
    for theme_name, fallback_keywords in fallback_map.items():
        if theme_name in topic:
            for kw in fallback_keywords:
                # 检查kw是否在scan_text里
                if kw in scan_text:
                    # 在theme_styles里找对应风格
                    matched_style = next((v for k, v in theme_styles.items() if k == kw), None)
                    if matched_style:
                        return matched_style, kw
                    # 在icons里找对应图标（用icons的style默认值）
                    if kw in icons:
                        return default, kw
    # 回退2：在完整内容中直接扫描所有theme_styles关键词
    for keyword, style in theme_styles.items():
        if keyword in scan_text:
            return style, keyword
    # 回退3：在完整内容中扫描icons关键词
    for keyword, icon in icons.items():
        if keyword in scan_text and keyword not in topic:
            return default, keyword
    return default, topic

def get_topic_icon(topic: str, full_content: str = "") -> str:
    """topic=主题标题, full_content=完整内容(含描述)，用于关键词回退扫描"""
    icons = get_topic_icons()
    scan_text = full_content if full_content else topic
    # 直接匹配
    for kw, icon in icons.items():
        if kw in topic:
            return icon
    # 回退1：fallback关键词优先
    fallback_map = CONFIG.get("theme_topic_fallback", {})
    for theme_name, fallback_keywords in fallback_map.items():
        if theme_name in topic:
            for kw in fallback_keywords:
                for keyword, icon in icons.items():
                    if keyword in scan_text:
                        return icon
    # 回退2：直接在完整内容中扫描所有icons关键词
    for keyword, icon in icons.items():
        if keyword in scan_text:
            return icon
    return "科技图表"

def analyze_topics(topics: list) -> dict:
    """topics: [(标题, 完整内容)]列表"""
    style_counts = {}
    topic_styles = []
    print(f"\n[智能分析] 主题数量: {len(topics)}")
    for topic_tuple in topics:
        if isinstance(topic_tuple, tuple):
            title, full_content = topic_tuple
        else:
            title, full_content = topic_tuple, topic_tuple
        style, matched_kw = detect_style_for_topic(title, full_content)
        ref_path = find_ref_image(style)
        topic_styles.append({"topic": title, "full": full_content, "style": style, "ref": ref_path, "label": matched_kw or title})
        style_counts[style] = style_counts.get(style, 0) + 1
        print(f"  - {title} → {style}{f' (原始词: {matched_kw})' if matched_kw and matched_kw != title else ''}")
    dominant = max(style_counts, key=style_counts.get)
    ref_images = []
    seen = set()
    for ts in topic_styles:
        if ts["ref"] and ts["ref"] not in seen:
            ref_images.append(ts["ref"])
            seen.add(ts["ref"])
    print(f"\n[风格统计]")
    for s, c in style_counts.items():
        print(f"  - {s}: {c}个主题")
    print(f"[参考图] {len(ref_images)}张")
    return {"topic_styles": topic_styles, "dominant_style": dominant, "ref_images": ref_images}

# ==================== 提示词组装（全部从yaml模板） ====================

def build_topic_visual_text(topics: list, layout_type: str) -> str:
    """根据布局组装逐格描述文本"""
    positions = get_layout_positions()
    layout_cfg = get_layout_assembly()
    default_cfg = layout_cfg.get("default", {})
    layout_specific = layout_cfg.get(layout_type, default_cfg)
    fmt = layout_specific.get("format", "numbered")
    prefix = layout_specific.get("prefix", "")

    slots = positions.get(layout_type, ["中央区域"])
    max_slots = len(slots)
    lines = []
    for i, topic in enumerate(topics[:max_slots]):
        # 标注用matched原始词(label)，不用主题标题(topic)
        label = topic.get("label", topic["topic"])
        title = topic["topic"]
        full = topic.get("full", title)
        icon = get_topic_icon(title, full)
        pos = slots[i]
        if fmt == "bullet":
            lines.append(f"- {pos}：{icon}，标注'{label}'")
        else:
            lines.append(f"{i+1}. {pos}：{icon}，标注'{label}'")

    # left4_right1 特殊：第5格是右侧大格
    if layout_type == "left4_right1":
        right_topic = topics[4] if len(topics) > 4 else topics[-1]
        label = right_topic.get("label", right_topic["topic"])
        title = right_topic["topic"]
        full = right_topic.get("full", title)
        lines.append(f"5. 右侧大格（突出总结区）：{get_topic_icon(title, full)}，标注'{label}'")

    text = "\n".join(lines)
    if prefix:
        text = f"{prefix}\n{text}"
    return text

def build_ref_descriptions(ref_images: list, dominant_style: str = None) -> str:
    """根据参考图反向查找风格key，再从style_bg_map取中文描述
    优先使用主风格（dominant_style）对应的描述，同名文件冲突时用主风格兜底"""
    parts = []
    srm = get_style_ref_map()
    bg_map = get_style_bg_map()
    # 优先风格key列表（主风格排前面，用于同名文件冲突时取主风格的描述）
    preferred_keys = []
    if dominant_style:
        preferred_keys.append(dominant_style)
    # 也把非xhs、非slide的原始主风格加进去
    for k in srm:
        if not k.startswith('xhs_') and not k.endswith('_slide') and not k.endswith('_style') and not k.endswith('_illustration'):
            if k not in preferred_keys:
                preferred_keys.append(k)
    # 反向查找：filename -> [style_keys]（可能多个）
    file_to_keys = {}
    for k, v in srm.items():
        if v not in file_to_keys:
            file_to_keys[v] = []
        file_to_keys[v].append(k)
    for i, ref_path in enumerate(ref_images, 1):
        fname = ref_path.name
        keys_for_file = file_to_keys.get(fname, [])
        # 优先用主风格匹配到的key，其次用第一个非变体key
        style_key = None
        for pk in preferred_keys:
            if pk in keys_for_file:
                style_key = pk
                break
        if not style_key and keys_for_file:
            style_key = keys_for_file[0]
        if not style_key:
            style_key = ref_path.stem
        style_desc = bg_map.get(style_key, "专业金融研报风格")
        parts.append(f"""## 参考图{i}（{ref_path.name}）:
- 风格: {style_desc}
- 严格遵循此参考图的配色方案、渲染风格、视觉元素
- 生成的图片必须看起来与参考图属于同一视觉系列""")
    return "\n".join(parts)

def build_bg_style(style: str) -> str:
    """获取风格背景描述，folder优先用yaml里的详细描述"""
    if style == "folder":
        desc = get_folder_style_desc()
        if desc:
            return desc
    bg_map = get_style_bg_map()
    return bg_map.get(style, "专业金融研报风格背景")

def get_layout_desc(layout_type: str) -> str:
    """获取布局的简洁描述"""
    layout_defs = CONFIG.get("layout_definitions", {})
    return layout_defs.get(layout_type, "网格布局")

def get_wechat_cover_rules() -> dict:
    """获取公众号封面规则"""
    return CONFIG.get("wechat_cover_rules", {})

def apply_wechat_title_rules(title: str, topics: list = None) -> str:
    """应用公众号标题规则：禁止词检查+最大长度+模板生成"""
    rules = get_wechat_cover_rules()
    max_len = rules.get("max_title_length", 13)
    forbidden_words = rules.get("forbidden_words", [])
    forbidden_titles = rules.get("forbidden_titles", [])

    # 禁止词检查
    for fw in forbidden_words:
        if fw in title:
            print(f"[WARN] 标题含禁止词'{fw}'，已替换")
            title = title.replace(fw, "**")
    for ft in forbidden_titles:
        if ft in title:
            print(f"[WARN] 标题为禁止标题'{ft}'，已替换")
            title = ft + "（违规）"

    # 长度截断
    if len(title) > max_len:
        title = title[:max_len]
        print(f"[WARN] 标题超过{max_len}字，已截断")

    return title

def build_prompt(analysis: dict, args) -> dict:
    """组装提示词——全部从yaml模板填充"""
    topics = analysis["merged_topics"] = analysis["topic_styles"]
    style = analysis["dominant_style"]
    ref_images = analysis["ref_images"]

    # 强制指定风格
    custom_style = getattr(args, "style", None) if args else None
    if custom_style and custom_style in get_style_ref_map():
        ref_path = REF_DIRS[0] / get_style_ref_map()[custom_style]
        if ref_path.exists():
            ref_images = [ref_path]
            style = custom_style

    # 布局选择
    topic_count = len(topics)
    custom_layout = getattr(args, "layout", None) if args else None
    if custom_layout:
        layout_type = custom_layout
        print(f"[INFO] 已使用指定布局：{layout_type}")
    else:
        layout_map = CONFIG.get("layout_by_topic_count", {})
        layout_type = layout_map.get(topic_count, layout_map.get("default", "top3_bottom2"))
        print(f"[INFO] 自动选择布局（{topic_count}个主题→{layout_type}）")

    # 标题
    platform = getattr(args, "platform", "toutiao") if args else "toutiao"
    aspect_ratio = get_aspect_ratio(platform)
    if platform == "wechat":
        aspect_ratio = "2.35:1"
        # 公众号标题统一由main函数处理（模板匹配+禁止词+长度限制），这里直接用
        main_title = getattr(args, "title", None) or "今日主线机会"
    else:
        # 非公众号平台
        if getattr(args, "title", None) and args.title:
            main_title = args.title
        else:
            main_title = "A股热点前瞻"
            candidates = [t["topic"] for t in topics if any(kw in t["topic"] for kw in ["机会", "赛道", "前瞻", "热点"])]
            if candidates:
                main_title = f"A股{''.join(candidates[:2])}"

    # 组装各部分（topics是dict列表，含label原始词，用于标注）
    topic_visual = build_topic_visual_text(topics, layout_type)
    bg_style = build_bg_style(style)
    layout_desc = get_layout_desc(layout_type)

    # 参考图描述：有图则注入参考图风格，无图则用默认描述
    ref_desc = build_ref_descriptions(ref_images, dominant_style=style)
    if ref_desc:
        ref_guide = f"参考图风格约束：\n{ref_desc}"
    else:
        ref_guide = "采用默认科技蓝图专业风格，保持配色统一、渲染精细"

    # 统一使用中文模板
    cn_template = CONFIG.get("cn_prompt_template", "")

    cn_prompt = cn_template.format(
        aspect_ratio=aspect_ratio,
        bg_style=bg_style,
        layout_desc=layout_desc,
        topic_visual=topic_visual,
        main_title=main_title,
        ref_guide=ref_guide,
    ) if cn_template else ""

    en_prompt = ""  # 已废弃，全部使用中文提示词

    print(f"[INFO] 适配平台：{platform}，使用比例：{aspect_ratio}")

    return {
        "cn": cn_prompt,
        "topics": "、".join([t["topic"] for t in topics]),
        "style": style,
        "ref_images": ref_images,
    }

# ==================== 报告解析 ====================

def extract_topics_from_report(report_path: Path) -> list:
    """提取主题，返回[(主题标题, 完整内容)]的列表"""
    for enc in ["utf-8", "utf-8-sig", "gbk", "gb2312"]:
        try:
            content = report_path.read_text(encoding=enc)
            break
        except:
            continue
    topics = []  # [(标题, 完整内容)]
    for pattern in [
        r'💎 主题：【(.+?)】',     # 捕获: 产能爆发
        r'主题：【(.+?)】',        # 捕获: 产能爆发
        r'【(.+?)】\+【(.+?)】',  # 捕获: (产能爆发, SpaceX万亿IPO+政策密集催化)
    ]:
        matches = re.findall(pattern, content)
        if matches:
            for m in matches:
                if isinstance(m, tuple):
                    # 第一个【】是主题标题，第二个是描述内容
                    title = m[0].strip()
                    full = m[0].strip() + '+' + m[1].strip()
                else:
                    title = m.strip().split('+')[0].strip()
                    full = m.strip()
                if title and (title, full) not in topics:
                    topics.append((title, full))
            if topics:
                break
    if not topics:
        for line in content.split('\n'):
            match = re.search(r'## .? .+?：(.+)', line)
            if match:
                t = match.group(1).strip()
                if t and len(t) < 20:
                    topics.append((t, t))
    return topics

def find_latest_report() -> Path:
    reports = sorted(REPORTS_DIR.glob("*.md"), key=os.path.getmtime, reverse=True)
    return reports[0] if reports else None

def copy_refs(ref_images: list, output_dir: Path) -> list:
    refs_dir = output_dir / "refs"
    refs_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for rp in ref_images:
        dest = refs_dir / rp.name
        shutil.copy2(rp, dest)
        copied.append(dest)
        print(f"  [复制参考图] {rp.name} → refs/")
    return copied

# ==================== 生图调用 ====================

def generate_image(prompt: str, output_path: Path, ref_images: list = None, model: str = "imagen") -> bool:
    import subprocess, json
    if model == "imagen" and not IMAGEN_SCRIPT.exists():
        print(f"[IMAGEN] ❌ 切换到autoglm")
        model = "autoglm"
    if model == "autoglm" and not AUTOGLM_SCRIPT.exists():
        print(f"[AUTOGLM] ❌ autoglm脚本不存在")
        return False
    try:
        if model == "imagen":
            cmd = [sys.executable, str(IMAGEN_SCRIPT), prompt, str(output_path)]
            if ref_images:
                for r in ref_images:
                    cmd.extend(["--ref", str(r)])
            print(f"[IMAGEN] 正在生成...")
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
        elif model == "autoglm":
            cmd = [sys.executable, str(AUTOGLM_SCRIPT), prompt]
            print(f"[AUTOGLM] 正在生成...")
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
            if result.returncode == 0:
                try:
                    resp = json.loads(result.stdout.strip())
                    img_url = resp.get("data", {}).get("image_url")
                    if img_url:
                        import requests
                        img_resp = requests.get(img_url, timeout=30)
                        if img_resp.status_code == 200:
                            with open(output_path, "wb") as f:
                                f.write(img_resp.content)
                            print(f"[AUTOGLM] ✅ 图片下载完成: {output_path.name}")
                            return True
                except Exception as e:
                    print(f"[AUTOGLM] ❌ 结果解析失败: {e}")
                    return False
        if result.returncode == 0:
            print(f"[{model.upper()}] ✅ 生成成功: {output_path.name}")
            return True
        else:
            print(f"[{model.upper()}] ❌ 生成失败: {result.stderr[:200]}")
            output_path.with_suffix(".prompt.txt").write_text(prompt, encoding="utf-8")
            return False
    except Exception as e:
        print(f"[{model.upper()}] ❌ 调用失败: {e}")
        output_path.with_suffix(".prompt.txt").write_text(prompt, encoding="utf-8")
        return False

# ==================== 主函数 ====================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="热点报告智能封面生成器（yaml驱动版）")
    parser.add_argument("--model", type=str, choices=["imagen", "autoglm"])
    parser.add_argument("--layout", type=str, help="指定布局")
    parser.add_argument("--style", type=str, help="指定风格")
    parser.add_argument("--platform", type=str, choices=["toutiao", "xhs", "wechat"], default="toutiao")
    parser.add_argument("--report", type=str, default="latest")
    parser.add_argument("--title", type=str)
    parser.add_argument("--article-dir", type=str)
    parser.add_argument("--cover", action="store_true")
    parser.add_argument("--illustrate", action="store_true")
    parser.add_argument("--prompt-only", action="store_true")
    parser.add_argument("--auto", "-a", action="store_true")
    args = parser.parse_args()

    # 模型检测
    available = []
    if IMAGEN_SCRIPT.exists(): available.append("imagen")
    if AUTOGLM_SCRIPT.exists(): available.append("autoglm")
    if not available and not args.prompt_only:
        print("❌ 未找到生图模型，请安装 imagen 或 autoglm-generate-image")
        return
    if not args.model: args.model = available[0] if available else None
    print(f"[INFO] 可用模型：{available}，使用：{args.model}")

    # 找报告
    if args.report == "latest":
        report_path = find_latest_report()
    else:
        report_path = REPORTS_DIR / args.report
    if not report_path or not report_path.exists():
        print(f"Error: 报告未找到: {args.report}")
        return
    print(f"[INFO] 读取报告: {report_path.name}")

    # 提取主题
    topics = extract_topics_from_report(report_path)
    if not topics:
        user_input = input("⚠️  未识别到主题，请手动输入（空格分隔）：> ").strip()
        if not user_input: return
        topics = [t.strip() for t in user_input.split() if t.strip()]
    elif len(topics) < 2:
        extra = input(f"⚠️  仅识别到 {len(topics)} 个：{topics}，补充？> ").strip()
        if extra: topics.extend([t.strip() for t in extra.split() if t.strip()])
    print(f"[INFO] 最终主题: {topics}")

    # ===== 封面模式 =====
    if args.cover or args.auto:
        print("\n[封面模式]")
        analysis = analyze_topics(topics)

        # 公众号标题自动生成
        if args.platform == "wechat" and not args.title:
            wechat = CONFIG.get("wechat_cover_rules", {})
            templates = wechat.get("title_templates", {})
            all_text = " ".join([t["topic"] for t in analysis["topic_styles"]])
            if any(kw in all_text for kw in templates.get("痛点型", {}).get("keywords", [])):
                args.title = templates["痛点型"]["pattern"]
            elif any(kw in all_text for kw in templates.get("利益型", {}).get("keywords", [])):
                args.title = templates["利益型"]["pattern"]
            elif any(kw in all_text for kw in templates.get("悬念型", {}).get("keywords", [])):
                args.title = templates["悬念型"]["pattern"]
            elif any(kw in str(report_path.name) for kw in templates.get("点题型", {}).get("report_patterns", [])):
                args.title = templates["点题型"]["pattern"]
            else:
                count_map = {1:"一大",2:"两大",3:"三大",4:"四大",5:"五大",6:"六大"}
                cw = count_map.get(len(topics), f"{len(topics)}大")
                args.title = templates.get("数字型", {}).get("pattern", "{count}大热点机会").format(count=cw)
            print(f"[INFO] 公众号标题：{args.title}")

        # 公众号规则校验：禁止词/标题用yaml配置（硬编码0）
        if args.platform == "wechat" and args.title:
            wechat = CONFIG.get("wechat_cover_rules", {})
            max_len = wechat.get("max_title_length", 13)
            if len(args.title) > max_len:
                args.title = args.title[:max_len]
            if args.title in wechat.get("forbidden_titles", []):
                print(f"[ERROR] 标题禁止使用，请修改")
                return
            for w in wechat.get("forbidden_words", []):
                if w in args.title:
                    print(f"[ERROR] 标题含敏感词'{w}'，请修改")
                    return

        prompt_data = build_prompt(analysis, args)
        print(f"\n{'='*60}")
        print(f"【封面提示词】主题: {prompt_data['topics']} | 风格: {prompt_data['style']} | 参考图: {len(prompt_data['ref_images'])}张")
        print(f"{'='*60}")

        if args.prompt_only:
            print(f"\n【提示词】\n{prompt_data['cn']}")
            return

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        dated = OUTPUT_DIR / datetime.now().strftime("%Y-%m-%d")
        dated.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%H%M%S")
        safe = re.sub(r'[\\/:*?"<>|]', '_', topics[0][0])[:15]
        output_path = dated / f"{ts}_cover_{safe}.png"
        copied = copy_refs(prompt_data["ref_images"], OUTPUT_DIR)

        success = generate_image(prompt_data["cn"], output_path, copied, model=args.model)
        if success:
            print(f"\n✅ 封面生成完成! 保存位置: {output_path}")
            if args.platform == "wechat" and args.article_dir:
                if CONFIG.get("wechat_cover_rules", {}).get("output_to_article_dir"):
                    dest = Path(args.article_dir) / f"封面_{output_path.name}"
                    if Path(args.article_dir).exists():
                        shutil.copy2(output_path, dest)
                        print(f"✅ 已复制到文章目录: {dest}")

    # ===== 配图模式 =====
    elif args.illustrate:
        print("\n[配图模式]")
        for t in topics:
            style = detect_style_for_topic(t)
            ref = find_ref_image(style)
            print(f"[处理] {t} → {style}")
            if ref: print(f"  [参考图] {ref.name}")
            if args.prompt_only: continue
            dated = OUTPUT_DIR / datetime.now().strftime("%Y-%m-%d")
            dated.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%H%M%S")
            output_path = dated / f"{ts}_{re.sub(r'[\\/:*?"<>|]', '_', t[:15])}.png"
            generate_image(f"""Create an illustration about「{t}". Style: {style}, 16:9, high quality 4K.""",
                          output_path, [ref] if ref else [], model=args.model)
        print("\n✅ 配图完成")

if __name__ == "__main__":
    main()
