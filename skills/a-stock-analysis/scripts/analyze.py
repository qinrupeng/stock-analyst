#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
A股实时行情与分时量能分析工具

数据源：新浪财经（统一接口）
支持：沪市(sh)、深市(sz) 股票

Usage:
    uv run analyze.py 600789              # 单只股票
    uv run analyze.py 600789 002446       # 多只股票
    uv run analyze.py 600789 --minute     # 分时量能分析
    uv run analyze.py 600789 --json       # JSON输出
"""

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def get_sina_symbol(code: str) -> str:
    """根据股票代码生成新浪格式代码"""
    code = code.upper().replace("SH", "").replace("SZ", "").replace(".", "")
    
    # 沪市: 6开头
    if code.startswith("6"):
        return "sh" + code
    # 深市: 0/3开头
    elif code.startswith(("0", "3")):
        return "sz" + code
    # 北交所: 8/4开头
    elif code.startswith(("8", "4")):
        return "bj" + code
    else:
        return "sh" + code


# 大盘指数 symbols（新浪格式）
MARKET_INDEX_SYMBOLS = "s_sh000001,s_sz399001,s_sz399006"
INDEX_NAMES = {
    "s_sh000001": "上证指数",
    "s_sz399001": "深证成指",
    "s_sz399006": "创业板指",
}


def fetch_market_indices() -> dict[str, dict]:
    """获取大盘指数实时行情
    
    返回格式: {symbol: {name, price, change, change_pct, volume, amount}}
    新浪s_前缀返回: 名称,点位,涨跌额,涨跌幅,成交量(万手),成交额(亿元)
    """
    result = {}
    try:
        url = f"https://hq.sinajs.cn/list={MARKET_INDEX_SYMBOLS}"
        req = urllib.request.Request(url, headers={
            "Referer": "https://finance.sina.com.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        })
        resp = urllib.request.urlopen(req, timeout=10)
        text = resp.read().decode("gbk")
        
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            match = re.match(r'var hq_str_(\w+)="([^"]*)"', line)
            if not match:
                continue
            sym = match.group(1)
            data = match.group(2)
            if not data or sym not in INDEX_NAMES:
                continue
            fields = data.split(",")
            if len(fields) < 3:
                continue
            result[sym] = {
                "name": INDEX_NAMES.get(sym, sym),
                "price": float(fields[1]) if fields[1] else 0,
                "change": float(fields[2]) if fields[2] else 0,
                "change_pct": float(fields[3]) if fields[3] else 0,
                "volume": float(fields[4]) if len(fields) > 4 and fields[4] else 0,
                "amount": float(fields[5]) if len(fields) > 5 and fields[5] else 0,
            }
    except Exception as e:
        print(f"大盘指数获取失败: {e}", file=sys.stderr)
    return result


def get_market_context(indices: dict[str, dict]) -> tuple[str, str]:
    """根据大盘指数判断市场环境
    
    Returns:
        (环境描述, 交易信号) - 如 ("三大指数全跌 市场偏弱", "谨慎做多")
    """
    if not indices:
        return "无法获取大盘数据", "信号不明"
    
    total_pct = sum(v["change_pct"] for v in indices.values())
    avg_pct = total_pct / len(indices)
    
    # 涨跌计数
    rises = sum(1 for v in indices.values() if v["change_pct"] > 0)
    falls = sum(1 for v in indices.values() if v["change_pct"] < 0)
    
    sh_pct = indices.get("s_sh000001", {}).get("change_pct", 0)
    chg = indices.get("s_sh000001", {}).get("change", 0)
    
    if avg_pct > 0.5:
        mood = "三大指数全涨 市场强势"
        signal = "积极做多"
    elif avg_pct > 0.1:
        mood = "多数指数上涨 市场偏强"
        signal = "可适当参与"
    elif avg_pct < -0.5:
        mood = "三大指数全跌 市场偏弱"
        signal = "控仓观望"
    elif avg_pct < -0.1:
        mood = "多数指数下跌 市场偏弱"
        signal = "谨慎操作"
    elif abs(avg_pct) <= 0.1:
        mood = "大盘震荡 方向不明"
        signal = "等待确认"
    else:
        mood = "市场分化"
        signal = "精选个股"
    
    return mood, signal


# ─────────────────────────────────────────────
# P1 新功能：Level2主力资金 / 板块阈值 / 止损止盈 / 生命周期
# ─────────────────────────────────────────────

def fetch_level2_flow(code: str) -> dict:
    """获取分钟级主力资金流向（东财免费接口，无需L2权限）
    
    返回格式:
    {
        "total_main": int,     # 全天主力净流入（元，负=净流出）
        "total_super": int,     # 超大单净流入
        "total_big": int,       # 大单净流入
        "total_mid": int,       # 中单净流入
        "total_small": int,     # 小单净流入
        "minute_data": [(time, main_net), ...],  # 分时序列
        "inflow_rate": float,   # 主力净流入占全市场比（%）
    }
    
    字段顺序(6字段): 时间,主力净流入,超大单净流入,大单净流入,中单净流入,小单净流入
    """
    secid = get_em_secid(code)
    url = (
        f"https://push2.eastmoney.com/api/qt/stock/fflow/kline/get"
        f"?lmt=0&klt=1"
        f"&fields1=f1,f2,f3"
        f"&fields2=f51,f52,f53,f54,f55,f56"
        f"&ut=7eea3edcaed734bea9c346148d8ab956"
        f"&secid={secid}"
    )
    result = {
        "total_main": 0, "total_super": 0, "total_big": 0,
        "total_mid": 0, "total_small": 0,
        "minute_data": [], "inflow_rate": 0.0,
    }
    try:
        req = urllib.request.Request(url, headers={
            "Referer": "https://data.eastmoney.com/",
            "User-Agent": "Mozilla/5.0",
        })
        resp = urllib.request.urlopen(req, timeout=10)
        text = resp.read().decode("utf-8")
        # 接口可能返回JSONP或纯JSON
        m = re.search(r'jQuery\((.+)\)', text)
        if m:
            data = json.loads(m.group(1))
        else:
            data = json.loads(text)
        klines = data.get("data", {}).get("klines", [])
        prev_main = prev_super = prev_big = prev_mid = prev_small = 0.0
        for item in klines:
            fields = item.split(",")
            if len(fields) < 6:
                continue
            t = fields[0]
            # East Money 返回的是当日累计值，需要差分得到单分钟真实流量
            cur_main = float(fields[1])
            cur_super = float(fields[2])
            cur_big = float(fields[3])
            cur_mid = float(fields[4])
            cur_small = float(fields[5])
            
            # 单分钟流量 = 当前累计 - 上次累计
            delta_main = cur_main - prev_main
            delta_super = cur_super - prev_super
            delta_big = cur_big - prev_big
            delta_mid = cur_mid - prev_mid
            delta_small = cur_small - prev_small
            
            result["minute_data"].append((t, delta_main))
            result["total_main"] += delta_main
            result["total_super"] += delta_super
            result["total_big"] += delta_big
            result["total_mid"] += delta_mid
            result["total_small"] += delta_small
            
            prev_main, prev_super, prev_big, prev_mid, prev_small = cur_main, cur_super, cur_big, cur_mid, cur_small
        
        # 计算净流入占比（相对全市场成交）
        total_abs = abs(result["total_main"])
        if result["minute_data"]:
            last_minute = result["minute_data"][-1][0]
            # 用全天成交额估算（简化版）
            total_amount_est = abs(result["total_main"]) + abs(result["total_small"])
            if total_amount_est > 0:
                result["inflow_rate"] = round(result["total_main"] / total_amount_est * 100, 2)
    except Exception as e:
        print(f"Level2资金流获取失败: {e}", file=sys.stderr)
    return result


def get_level2_signal(flow: dict, market_pct: float = 0) -> list[str]:
    """根据Level2资金流返回多空博弈信号
    
    四档资金定义:
    - 超大单: 金额>100万的主动买入/卖出
    - 大单: 金额20-100万的主动买入/卖出
    - 中单: 金额5-20万
    - 小单: 金额<5万
    """
    signals = []
    if not flow["minute_data"]:
        return signals
    
    total = flow["total_main"]
    super_large = flow["total_super"]
    big = flow["total_big"]
    mid = flow["total_mid"]
    small = flow["total_small"]
    
    # ── 第一层：主力总流向（EastMoney计算口径，可能含"其他"档位）──
    institution_net = super_large + big
    retail_net = total - institution_net  # 散户 = 主力 - 机构
    
    if total > 1e8:
        sig = f"✅ 主力净流入: {total/1e8:+.2f}亿"
        if institution_net > 0:
            sig += "（机构/超大单主导，真金白银）"
        else:
            sig += "（含隐性买盘（庄家/配资/量化），非散户主导）"
        signals.append(sig)
    elif total < -1e8:
        sig = f"⚠️ 主力净流出: {total/1e8:+.2f}亿"
        if institution_net < 0:
            sig += "（机构/超大单主导，主力出货）"
        else:
            sig += "（含隐性卖盘，非散户恐慌）"
        signals.append(sig)
    
    # ── 第二层：多空博弈（四档资金分析）──
    if institution_net > 5e7 and retail_net < -1e7:
        signals.append("🥊 多空博弈: 机构净买入 + 散户净卖出 → 机构吃筹，筹码从散户流向机构")
    elif institution_net < -5e7 and retail_net > 1e7:
        signals.append("🥊 多空博弈: 机构净卖出 + 散户净买入 → 机构派发，筹码从机构流向散户")
    elif abs(institution_net) < 2e7 and abs(retail_net) < 2e7:
        signals.append("🥊 多空博弈: 多空均衡，双方都在观望")
    
    # 超大单单独分析（机构中的机构，最强信号）
    if super_large > 3e7:
        signals.append(f"  └ 超大单: {super_large/1e8:+.2f}亿（大资金动向）")
    elif super_large < -3e7:
        signals.append(f"  └ 超大单: {super_large/1e8:+.2f}亿（大资金撤退）")
    
    # ── 第三层：尾盘15分钟资金博弈 ──
    mins = flow["minute_data"]
    if len(mins) >= 15:
        last_15 = sum(m for _, m in mins[-15:])
        if last_15 > 3e7:
            signals.append(f"🔥 尾盘15分钟主力净流入: {last_15/1e6:+.0f}万（尾盘做多）")
        elif last_15 < -3e7:
            signals.append(f"🔻 尾盘15分钟主力净流出: {last_15/1e6:+.0f}万（尾盘减仓）")
    
    return signals


def format_level2(flow: dict, signals: list[str]) -> str:
    """格式化Level2资金流完整输出（视觉化版本）"""
    if not flow["minute_data"]:
        return "\n【Level2主力资金】数据获取失败"
    
    total_main = flow["total_main"]
    total_super = flow["total_super"]
    total_big = flow["total_big"]
    total_mid = flow["total_mid"]
    total_small = flow["total_small"]
    
    # 找最大绝对值用于归一化
    max_val = max(abs(total_super), abs(total_big), abs(total_mid), abs(total_small))
    bar_width = 16
    
    def flow_bar(val: float) -> str:
        if max_val == 0:
            return "░" * bar_width
        pct = abs(val) / max_val
        filled = int(pct * bar_width)
        sign = "▲" if val >= 0 else "▼"
        return sign + "█" * filled + "░" * (bar_width - filled)
    
    # 净流入方向icon
    main_icon = "🟢" if total_main >= 0 else "🔴"
    main_label = "净流入" if total_main >= 0 else "净流出"
    
    lines = [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"💰 Level2资金流  {main_icon} 主力{main_label}: {total_main/1e8:+.2f}亿",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"  超大单  {flow_bar(total_super)}  {total_super/1e8:+.2f}亿",
        f"  大单    {flow_bar(total_big)}  {total_big/1e8:+.2f}亿",
        f"  中单    {flow_bar(total_mid)}  {total_mid/1e8:+.2f}亿",
        f"  小单    {flow_bar(total_small)}  {total_small/1e8:+.2f}亿",
    ]
    
    if signals:
        lines.append("")
        for sig in signals:
            lines.append(f"  {sig}")
    
    return "\n".join(lines)


def get_board_limits(code: str) -> tuple[float, float]:
    """根据板块返回涨跌停阈值（用于量能分布判断）
    
    Returns: (涨停幅度%, 跌停幅度%)
    """
    board = get_board_type(code)
    limits = {
        "主板": (10.0, 10.0),
        "科创板": (20.0, 20.0),
        "创业板": (20.0, 20.0),
        "北交所": (30.0, 30.0),
    }
    return limits.get(board, (10.0, 10.0))


def calculate_support_resistance(code: str) -> dict:
    """计算当日支撑/压力位 + 布林带（用于止损止盈参考）
    
    基于当日分时高低点 + 最近N日布林带
    """
    import math
    
    # 获取日K数据（最近20天）
    daily = fetch_daily_data_em(code, days=20)
    if not daily or len(daily) < 5:
        return {}
    
    closes = [d["close"] for d in daily]
    
    # 布林带（20日）
    period = min(20, len(closes))
    ma20 = sum(closes[-period:]) / period
    variance = sum((c - ma20) ** 2 for c in closes[-period:]) / period
    std20 = math.sqrt(variance)
    upper_band = round(ma20 + 2 * std20, 2)
    lower_band = round(ma20 - 2 * std20, 2)
    
    # 当日高低点（从分时数据）
    minute_data, _ = fetch_minute_data("sina", get_sina_symbol(code), code, count=500)
    if not minute_data:
        return {"bollinger": {"upper": upper_band, "ma20": round(ma20, 2), "lower": lower_band}}
    
    day_high = max((d["high"] for d in minute_data), default=0)
    day_low = min((d["low"] for d in minute_data), default=0)
    current = minute_data[-1]["close"] if minute_data else 0
    
    # 支撑/压力计算
    today_range = day_high - day_low
    support1 = round(day_low + today_range * 0.236, 2)   # 23.6%黄金分割
    support2 = round(day_low + today_range * 0.382, 2)   # 38.2%
    resistance1 = round(day_high - today_range * 0.236, 2)
    resistance2 = round(day_high - today_range * 0.382, 2)
    
    # 止损参考（跌破支撑2%）
    stop_loss = round(support1 * 0.98, 2)
    # 止盈参考（接近压力位或布林上轨）
    take_profit = min(resistance1, upper_band)
    
    return {
        "bollinger": {
            "upper": upper_band,
            "ma20": round(ma20, 2),
            "lower": lower_band,
        },
        "today": {
            "high": round(day_high, 2),
            "low": round(day_low, 2),
            "current": round(current, 2),
            "support1": support1,
            "support2": support2,
            "resistance1": resistance1,
            "resistance2": resistance2,
            "stop_loss": stop_loss,
            "take_profit": round(take_profit, 2),
        },
    }


def format_support_resistance(sr: dict) -> str:
    """格式化支撑压力位输出（视觉化版本）"""
    if not sr:
        return ""
    
    bb = sr.get("bollinger", {})
    today = sr.get("today", {})
    
    lines = [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "📍 参考价位",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    
    if bb:
        lines.append(f"  布林带(20日)  上={bb['upper']}  中={bb['ma20']}  下={bb['lower']}")
    
    if today:
        current = today.get("current", 0)
        resistance1 = today.get("resistance1", 0)
        support1 = today.get("support1", 0)
        stop_loss = today.get("stop_loss", 0)
        take_profit = today.get("take_profit", 0)
        
        lines.append(f"  今日区间  {today.get('high')}（高） / {today.get('low')}（低）")
        lines.append("")
        lines.append(f"  🔴 压力位   {resistance1:.2f}")
        lines.append(f"  🟡 今日价   {current:.2f}")
        lines.append(f"  🟢 支撑位   {support1:.2f}")
        lines.append("")
        lines.append(f"  ⚠️ 止损参考  {stop_loss:.2f}  (跌破则离场)")
        lines.append(f"  🎯 止盈参考  {take_profit:.2f}  (接近可考虑减仓)")
    
    return "\n".join(lines)


def detect_lifecycle_stage(code: str) -> dict:
    """识别个股热点生命周期阶段（萌芽/爆发/成熟/衰退）
    
    基于近5日成交量趋势 + 换手率变化 + 价格动量
    """
    daily = fetch_daily_data_em(code, days=10)
    if not daily or len(daily) < 5:
        return {}
    
    volumes = [d["volume"] for d in daily]
    closes = [d["close"] for d in daily]
    amounts = [d["amount"] for d in daily]
    
    # 近3日均值 vs 前5日均值（量能趋势）
    recent_vol = sum(volumes[-3:]) / 3
    past_vol = sum(volumes[-6:-3]) / 3 if len(volumes) >= 6 else recent_vol
    vol_ratio = recent_vol / past_vol if past_vol > 0 else 1.0
    
    # 价格动量（近3日涨跌）
    price_chg = (closes[-1] - closes[-4]) / closes[-4] * 100 if len(closes) >= 4 else 0
    
    # 换手率估算（成交额/收盘市值）
    est_turnover = [am / (cl * vol) if cl * vol > 0 else 0
                    for am, cl, vol in zip(amounts, closes, volumes)]
    avg_turnover = sum(est_turnover[-3:]) / 3 if len(est_turnover) >= 3 else 0
    
    # 判断阶段
    if vol_ratio > 2.0 and price_chg > 10:
        stage = "爆发期"
        desc = f"量能激增{vl_to_text(vol_ratio)}，价格强势上涨{price_chg:.1f}%，大概率处于主升浪初期"
    elif vol_ratio > 1.5 and price_chg > 5:
        stage = "成熟期"
        desc = f"量能维持高位，价格上涨{price_chg:.1f}%，可能处于主升浪中后期，注意回调风险"
    elif vol_ratio < 0.7 and price_chg < -5:
        stage = "衰退期"
        desc = f"量能萎缩至前期的{vl_to_text(vol_ratio)}，价格下跌{price_chg:.1f}%，主线退潮"
    elif vol_ratio > 1.2 and -3 < price_chg < 3:
        stage = "萌芽期"
        desc = f"量能温和放大({vl_to_text(vol_ratio)}倍)，价格横盘，可能在建仓阶段"
    else:
        stage = "震荡期"
        desc = f"量能平稳，价格小幅变动{price_chg:.1f}%，方向不明"
    
    return {
        "stage": stage,
        "description": desc,
        "vol_ratio_3d_vs_5d": round(vol_ratio, 2),
        "price_momentum_3d": round(price_chg, 2),
        "est_turnover": round(avg_turnover * 100, 2),  # 转为百分比
    }


def vl_to_text(ratio: float) -> str:
    """量能比转文字"""
    if ratio > 3:
        return "3倍以上"
    elif ratio > 2:
        return "2倍以上"
    elif ratio > 1.5:
        return "1.5倍以上"
    elif ratio > 1.2:
        return "1.2倍以上"
    elif ratio > 0.8:
        return "相近"
    elif ratio > 0.5:
        return "萎缩至六成"
    else:
        return "萎缩至四成以下"


def format_lifecycle(stage_info: dict) -> str:
    """格式化生命周期输出（视觉化版本）"""
    if not stage_info:
        return ""
    
    stage = stage_info["stage"]
    stage_icons = {
        "萌芽期": "🌱",
        "爆发期": "🚀",
        "成熟期": "🔥",
        "衰退期": "💤",
        "震荡期": "⚖️",
    }
    icon = stage_icons.get(stage, "⚪")
    
    vol_ratio = stage_info.get("vol_ratio_3d_vs_5d", 0)
    price_momentum = stage_info.get("price_momentum_3d", 0)
    
    # 量能比条形图
    max_ratio = max(vol_ratio, 2.0)  # 标准化到2x满格
    vol_bar_len = min(int(vol_ratio / max_ratio * 16), 16)
    vol_bar = "█" * vol_bar_len + "░" * (16 - vol_bar_len)
    
    # 价格动量颜色
    if price_momentum > 5:
        price_icon = "▲▲"
        price_color = "🔴"
    elif price_momentum > 0:
        price_icon = "▲"
        price_color = "🟡"
    elif price_momentum < -5:
        price_icon = "▼▼"
        price_color = "🔴"
    else:
        price_icon = "▼"
        price_color = "🟢"
    
    lines = [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🌡️ 热点生命周期  {icon} {stage}",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"  {stage_info['description']}",
        "",
        f"  量能比(近3日/前5日)  {vol_bar}  {vol_ratio:.2f}x",
        f"  价格动量(近3日)      {price_color} {price_icon} {price_momentum:+.1f}%",
    ]
    return "\n".join(lines)


def fetch_realtime_sina(symbols: list[str]) -> dict[str, dict]:
    """从新浪获取实时行情（支持批量）
    
    新浪接口返回格式:
    var hq_str_sh600789="名称,今开,昨收,现价,最高,最低,买一,卖一,成交量(股),成交额(元),...";
    
    字段说明:
    0: 名称
    1: 今开
    2: 昨收  
    3: 现价
    4: 最高
    5: 最低
    6: 买一价
    7: 卖一价
    8: 成交量(股)
    9: 成交额(元)
    """
    result = {}
    
    try:
        codes_str = ",".join(symbols)
        url = f"https://hq.sinajs.cn/list={codes_str}"
        
        req = urllib.request.Request(url, headers={
            "Referer": "https://finance.sina.com.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        })
        resp = urllib.request.urlopen(req, timeout=10)
        text = resp.read().decode("gbk")
        
        # 解析每行
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            
            # var hq_str_sh600789="数据";
            match = re.match(r'var hq_str_(\w+)="([^"]*)"', line)
            if not match:
                continue
            
            symbol = match.group(1)
            data_str = match.group(2)
            
            if not data_str:
                continue
            
            fields = data_str.split(",")
            if len(fields) < 32:
                continue
            
            name = fields[0]
            open_price = float(fields[1]) if fields[1] else None
            pre_close = float(fields[2]) if fields[2] else None
            price = float(fields[3]) if fields[3] else None
            high = float(fields[4]) if fields[4] else None
            low = float(fields[5]) if fields[5] else None
            volume = int(float(fields[8])) if fields[8] else 0  # 股
            amount = float(fields[9]) if fields[9] else 0  # 元
            
            if not price or price <= 0:
                continue
            
            # 计算涨跌
            change_amt = price - pre_close if pre_close else 0
            change_pct = (change_amt / pre_close * 100) if pre_close and pre_close > 0 else 0
            
            # 换手率需要总股本，这里先留空
            result[symbol] = {
                "code": symbol[2:],  # 去掉sh/sz前缀
                "name": name,
                "price": price,
                "open": open_price,
                "pre_close": pre_close,
                "high": high,
                "low": low,
                "volume": volume // 100,  # 转换为手
                "amount": amount,
                "change_amt": round(change_amt, 2),
                "change_pct": round(change_pct, 2),
                "turnover": None,  # 新浪实时接口不提供换手率
            }
            
    except Exception as e:
        print(f"新浪实时接口错误: {e}", file=sys.stderr)
    
    return result


def fetch_minute_data_sina(symbol: str, count: int = 500) -> list[dict]:
    """从新浪获取分时K线数据
    
    接口: CN_MarketDataService.getKLineData
    返回JSON数组，每条记录包含:
    - day: 时间 (2026-01-27 09:31:00)
    - open/high/low/close: OHLC价格
    - volume: 成交量(股)
    - amount: 成交额(元)
    
    注意: A股交易时段09:15-15:00共350分钟，默认500条余量足够覆盖全天
    """
    url = f"https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_{symbol}=/CN_MarketDataService.getKLineData?symbol={symbol}&scale=1&ma=no&datalen={count}"
    
    try:
        req = urllib.request.Request(url, headers={
            "Referer": "https://finance.sina.com.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        resp = urllib.request.urlopen(req, timeout=10)
        text = resp.read().decode("utf-8")
        
        # 解析JSONP: var _xxx=([...])
        match = re.search(r"\(\[(.*)\]\)", text, re.DOTALL)
        if not match:
            return []
        
        data = json.loads("[" + match.group(1) + "]")
        result = []
        for item in data:
            result.append({
                "time": item["day"],
                "open": float(item["open"]),
                "high": float(item["high"]),
                "low": float(item["low"]),
                "close": float(item["close"]),
                "volume": int(item["volume"]),  # 股
                "amount": float(item["amount"]),  # 元
            })
        return result
        
    except Exception as e:
        print(f"新浪分时接口错误: {e}", file=sys.stderr)
    
    return []


def get_board_type(code: str) -> str:
    """根据股票代码识别板块类型，返回涨跌停限制和量能阈值说明
    
    - 主板(沪深): 10% 涨跌停
    - 科创板: 20% 涨跌停
    - 创业板: 20% 涨跌停（注册制）
    - 北交所: 30% 涨跌停（新股前N天规则复杂，此处用30%）
    """
    code = code.upper().replace("SH", "").replace("SZ", "").replace(".", "").replace("BJ", "")
    if code.startswith("688"):
        return "科创板"   # 20% 涨跌停
    elif code.startswith(("430", "830", "870")):
        return "北交所"   # 30% 涨跌停（简化）
    elif code.startswith("3"):
        return "创业板"   # 20% 涨跌停
    else:
        return "主板"     # 10% 涨跌停


def get_em_secid(code: str) -> str:
    """根据股票代码生成东方财富 secid
    
    secid格式：市场代码.股票代码
    沪市: 1.x (6开头，含688科创)
    深市: 0.x (0/2/3开头)
    北交所: 0.x (4/8开头)
    """
    code = code.upper().replace("SH", "").replace("SZ", "").replace(".", "").replace("BJ", "")
    if code.startswith(("6",)):
        return f"1.{code}"
    elif code.startswith(("0", "3", "8", "4")):
        return f"0.{code}"
    else:
        return f"1.{code}"


def fetch_minute_data_em(code: str, count: int = 250) -> list[dict]:
    """从东方财富获取分时K线数据（备用源）
    
    接口: push2his.eastmoney.com
    返回格式: "时间,开,收,高,低,成交量,成交额,..."
    
    字段映射(f51-f61):
    0:时间, 1:开盘, 2:收盘, 3:最高, 4:最低, 5:成交量(手), 6:成交额
    """
    secid = get_em_secid(code)
    # 取今日数据
    today = datetime.now().strftime("%Y%m%d")
    url = (
        f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
        f"?secid={secid}"
        f"&fields1=f1,f2,f3,f4,f5,f6"
        f"&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
        f"&klt=1&fqt=1&beg={today}&end={today}"
        f"&smplmt=460&lmt=1000000"
    )
    
    try:
        req = urllib.request.Request(url, headers={
            "Referer": "https://finance.eastmoney.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        })
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode("utf-8"))
        
        klines = data.get("data", {}).get("klines", [])
        result = []
        for item in klines:
            fields = item.split(",")
            if len(fields) < 7:
                continue
            result.append({
                "time": fields[0],       # "2026-03-26 09:31"
                "open": float(fields[1]),
                "close": float(fields[2]),
                "high": float(fields[3]),
                "low": float(fields[4]),
                "volume": int(float(fields[5])) * 100,  # 东财是手，转为股
                "amount": float(fields[6]),
            })
        return result
        
    except Exception as e:
        print(f"东财分时接口错误: {e}", file=sys.stderr)
    
    return []


def fetch_minute_data(source: str, symbol: str, code: str, count: int = 500) -> tuple[list[dict], str]:
    """获取分时数据，东财为主源（覆盖完整时段），新浪备用
    
    注意：东财接口返回完整分时，优先使用；新浪有250条记录限制
    Returns:
        (data, source): 分时数据列表和数据来源标识
    """
    # 东财优先：覆盖完整，不丢早盘数据
    data = fetch_minute_data_em(code, count)
    if data:
        return data, "东方财富"
    
    # 备用：新浪
    data = fetch_minute_data_sina(symbol, count)
    if data:
        return data, "新浪"
    
    return [], "无数据"


def analyze_minute_volume(minute_data: list[dict], market_change_pct: float = 0) -> dict:
    """分析分时量能
    
    时间过滤逻辑（修复Bug）：
    - 新浪分时数据格式：YYYY-MM-DD HH:MM:SS
    - 用正则提取 HH:MM 再比较，避免切片错位问题
    - 集合竞价 09:15-09:25 允许通过（有真实成交）
    """
    if not minute_data:
        return {"error": "无分时数据"}
    
    def extract_time(dt_str: str) -> str:
        """从时间字符串提取 HH:MM，兼容新浪(含秒)和东财(不含秒)格式"""
        # 新浪: "2026-03-26 10:29:00" → 匹配 HH:MM:SS
        m = re.search(r'\d{4}-\d{2}-\d{2}\s+(\d{2}:\d{2}):\d{2}', dt_str)
        if m:
            return m.group(1)
        # 东财: "2026-03-26 09:31" → 匹配 HH:MM
        m = re.search(r'\d{4}-\d{2}-\d{2}\s+(\d{2}:\d{2})(?::\d{2})?$', dt_str)
        return m.group(1) if m else ""
    
    def time_in_range(dt_str: str, start: str, end: str) -> bool:
        """判断 HH:MM 是否在 [start, end) 区间"""
        t = extract_time(dt_str)
        return start <= t < end
    
    # 过滤交易时段数据（09:15-15:00，含集合竞价）
    trading_data = [
        d for d in minute_data
        if d["volume"] > 0 and time_in_range(d["time"], "09:15", "15:01")
    ]
    
    if not trading_data:
        return {"error": "无有效交易数据"}
    
    # 统计各时段成交量
    total_vol = sum(d["volume"] for d in trading_data)
    
    def period_vol(start: str, end: str) -> int:
        return sum(
            d["volume"] for d in trading_data
            if time_in_range(d["time"], start, end)
        )
    
    open_30 = period_vol("09:30", "10:00")
    mid_am = period_vol("10:00", "11:30")
    mid_pm = period_vol("13:00", "14:30")
    close_30 = period_vol("14:30", "15:01")
    
    # 放量时段 TOP 10
    sorted_by_vol = sorted(trading_data, key=lambda x: x["volume"], reverse=True)[:10]
    top_volumes = [
        {
            "time": extract_time(d["time"]),
            "price": d["close"],
            "volume": d["volume"] // 100,  # 转换为手
            "amount": d["amount"],
        }
        for d in sorted_by_vol
    ]
    
    # 主力动向判断（增强版：结合大盘环境）
    signals = []
    stock_up = any(d["close"] > d["open"] for d in trading_data[-10:] if "open" in d)
    stock_change_pct = 0  # 简化：粗估当日涨跌幅方向
    if trading_data and trading_data[-1]["close"] and trading_data[0]["close"]:
        stock_change_pct = (trading_data[-1]["close"] - trading_data[0]["close"]) / trading_data[0]["close"] * 100

    if total_vol > 0:
        if close_30 / total_vol > 0.25:
            if market_change_pct < -0.3:
                signals.append("⚠️ 尾盘大幅放量+大盘走弱，可能是主力拉高出货")
            elif stock_change_pct < 0 and market_change_pct > 0:
                signals.append("⚠️ 尾盘大幅放量+该股走弱但大盘走强，留意主力出货")
            else:
                signals.append("尾盘大幅放量，可能有主力抢筹或出货")
        elif close_30 / total_vol > 0.15:
            signals.append("尾盘有一定放量")
        
        if open_30 / total_vol > 0.30:
            if market_change_pct < -0.5 and stock_change_pct < 0:
                signals.append("⚠️ 大盘弱势+该股走弱+早盘放量，警惕主力砸盘")
            elif market_change_pct > 0 and stock_change_pct > 1:
                signals.append("✅ 大盘强势+该股领涨+早盘放量，主力真正抢筹信号")
            else:
                signals.append("早盘主力抢筹明显（需结合大盘判断强度）")
        if open_30 / total_vol > 0.40:
            if market_change_pct < -0.3:
                signals.append("⚠️ 早盘异常放量+大盘大跌，谨慎！可能是对倒或诱多")
            elif stock_change_pct > 2:
                signals.append("🚀 早盘异常放量+强势上涨，主力强势介入")
            else:
                signals.append("早盘放量异常，主力介入信号（建议结合日线判断）")
    
    # 检测涨停/跌停：high == low 说明全天价格凝固在单一价位（封板特征）
    if trading_data:
        highs = [d["high"] for d in trading_data]
        lows = [d["low"] for d in trading_data]
        last_close = trading_data[-1]["close"]
        day_high = max(highs)
        day_low = min(lows)
        if day_high == day_low and day_high == last_close and day_high > 0:
            # 全天只有一种价格，且等于收盘价 = 封板
            signals.append("疑似封板（涨停或跌停），请以实际行情为准")
    
    return {
        "total_volume": total_vol // 100,  # 手
        "total_amount": sum(d["amount"] for d in trading_data),
        "distribution": {
            "open_30min": {
                "volume": open_30 // 100,
                "percent": round(open_30 / total_vol * 100, 1) if total_vol else 0,
            },
            "mid_am": {
                "volume": mid_am // 100,
                "percent": round(mid_am / total_vol * 100, 1) if total_vol else 0,
            },
            "mid_pm": {
                "volume": mid_pm // 100,
                "percent": round(mid_pm / total_vol * 100, 1) if total_vol else 0,
            },
            "close_30min": {
                "volume": close_30 // 100,
                "percent": round(close_30 / total_vol * 100, 1) if total_vol else 0,
            },
        },
        "top_volumes": top_volumes,
        "signals": signals,
    }


def get_watch_file(code: str) -> Path:
    """获取股票监控状态文件路径"""
    return Path.home() / ".clawdbot" / "skills" / "a-stock-analysis" / f"watch_{code}.json"


def load_watch_state(code: str) -> dict | None:
    """加载上次运行状态"""
    f = get_watch_file(code)
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def save_watch_state(code: str, state: dict):
    """保存当前运行状态"""
    f = get_watch_file(code)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def diff_watch(code: str, current: dict) -> list[str]:
    """对比上次状态，返回告警列表"""
    prev = load_watch_state(code)
    alerts = []
    if not prev:
        alerts.append(f"初次记录: {current['name']}({code}) 现价={current['price']:.2f}")
    else:
        prev_price = prev.get("price", 0)
        curr_price = current["price"]
        if prev_price > 0:
            pct = (curr_price - prev_price) / prev_price * 100
            abs_chg = curr_price - prev_price
            if abs(abs_chg) >= 0.05:  # 涨跌超过5分钱
                direction = "🚀 上涨" if abs_chg > 0 else "🔻 下跌"
                alerts.append(f"{direction}: {current['name']}({code}) {prev_price:.2f} → {curr_price:.2f} ({pct:+.2f}%)")
            # 监控RSI超买超卖变化
            prev_rsi = prev.get("rsi14")
            curr_rsi = current.get("rsi14")
            if prev_rsi is not None and curr_rsi is not None:
                if prev_rsi >= 70 and curr_rsi < 70:
                    alerts.append(f"⚠️ RSI脱离超买区: {current['name']} {prev_rsi}→{curr_rsi}")
                elif prev_rsi <= 30 and curr_rsi > 30:
                    alerts.append(f"⚠️ RSI脱离超卖区: {current['name']} {prev_rsi}→{curr_rsi}")
                elif curr_rsi > 70:
                    alerts.append(f"⚠️ RSI超买: {current['name']} RSI={curr_rsi}")
                elif curr_rsi < 30:
                    alerts.append(f"⚠️ RSI超卖: {current['name']} RSI={curr_rsi}")
    return alerts


def fetch_daily_data_em(code: str, days: int = 60) -> list[dict]:
    """从东方财富获取日K线数据（用于技术指标计算）
    
    返回格式: [{date, open, close, high, low, volume, amount}, ...]
    """
    secid = get_em_secid(code)
    end = datetime.now().strftime("%Y%m%d")
    beg = (datetime.now().replace(day=1) - timedelta(days=days*2)).strftime("%Y%m%d")
    url = (
        f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
        f"?secid={secid}"
        f"&fields1=f1,f2,f3,f4,f5,f6"
        f"&fields2=f51,f52,f53,f54,f55,f56,f57"
        f"&klt=101&fqt=1&beg={beg}&end={end}&lmt={days}"
    )
    try:
        req = urllib.request.Request(url, headers={
            "Referer": "https://finance.eastmoney.com/",
            "User-Agent": "Mozilla/5.0",
        })
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode("utf-8"))
        klines = data.get("data", {}).get("klines", [])
        result = []
        for item in klines:
            fields = item.split(",")
            if len(fields) < 6:
                continue
            result.append({
                "date": fields[0],
                "open": float(fields[1]),
                "close": float(fields[2]),
                "high": float(fields[3]),
                "low": float(fields[4]),
                "volume": int(float(fields[5])),
                "amount": float(fields[6]) if len(fields) > 6 else 0,
            })
        return result
    except Exception as e:
        print(f"东财日K接口错误: {e}", file=sys.stderr)
    return []


def calculate_rsi(closes: list[float], period: int = 14) -> float | None:
    """计算RSI相对强弱指标"""
    if len(closes) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
    if len(gains) < period:
        return None
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def calculate_macd(closes: list[float], fast: int = 12, slow: int = 26, signal: int = 9) -> dict | None:
    """计算MACD指标，返回 {macd, signal, histogram}"""
    if len(closes) < slow + signal:
        return None
    
    def ema(data: list[float], period: int) -> list[float]:
        k = 2 / (period + 1)
        result = [data[0]]
        for i in range(1, len(data)):
            result.append(data[i] * k + result[-1] * (1 - k))
        return result
    
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    macd_line = [ema_fast[i] - ema_slow[i] for i in range(len(closes))]
    macd_ema = ema(macd_line[-slow:], signal)
    # signal线对齐macd线
    signal_line = [macd_ema[0]] * (len(macd_line) - signal) + macd_ema
    
    n = len(macd_line)
    macd_val = round(macd_line[-1], 4)
    signal_val = round(signal_line[-1], 4)
    hist = round(macd_line[-1] - signal_line[-1], 4)
    return {
        "macd": macd_val,
        "signal": signal_val,
        "histogram": hist,
        "histogram_pct": round(hist / closes[-1] * 100, 3) if closes[-1] else 0,
    }


def fetch_stock_profile_em(code: str) -> dict:
    """从东财获取股票基本面数据（市值/PE/换手率/近5日主力流向）
    
    f162: 流通市值(万元)
    f167: 换手率(%)
    f168: 动态市盈率
    f173: 量比
    f178: 近5日主力资金流向历史
    """
    secid = get_em_secid(code)
    url = (
        f"https://push2.eastmoney.com/api/qt/stock/get"
        f"?secid={secid}"
        f"&fields=f57,f58,f162,f167,f168,f170,f173,f178"
    )
    try:
        req = urllib.request.Request(url, headers={
            "Referer": "https://data.eastmoney.com/",
            "User-Agent": "Mozilla/5.0",
        })
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode("utf-8"))
        d = data.get("data", {})
        if not d:
            return {}
        
        # 解析近5日主力资金流向
        flow_hist = []
        raw_hist = d.get("f178", "[]")
        if raw_hist and isinstance(raw_hist, str):
            try:
                flow_list = json.loads(raw_hist)
                for f in flow_list:
                    flow_hist.append({
                        "date": f.get("date", ""),
                        "main_net": f.get("mainNetAmt", 0),
                    })
            except Exception:
                pass
        
        # 连续3日净流出检测
        neg_days = 0
        for f in flow_hist[:3]:
            if f["main_net"] < 0:
                neg_days += 1
        
        return {
            "circ_market_cap": d.get("f162", 0),      # 流通市值（亿元），经茅台交叉验证
            "pe": d.get("f168", 0),                   # 动态市盈率
            "vol_ratio": d.get("f173", 0),            # 量比
            "flow_hist": flow_hist,                   # 近5日主力资金
            "consecutive_outflow_3d": neg_days >= 3,  # 连续3日净流出
        }
    except Exception as e:
        print(f"Stock profile获取失败: {e}", file=sys.stderr)
    return {}


def get_risk_signals(profile: dict, change_pct: float, tech: dict) -> list[tuple[str, str, str]]:
    """检测七大风险信号
    
    Returns: [(icon, risk_type, description), ...]
    """
    risks = []
    
    # 1. 估值风险：连续3日涨幅≥30% 或 PE≥100
    if profile.get("pe", 0) >= 100:
        risks.append(("🔴", "估值风险", f"PE={profile['pe']}，估值偏高"))
    
    # 2. 资金风险：连续3日主力净流出
    if profile.get("consecutive_outflow_3d"):
        risks.append(("🔴", "资金风险", "连续3日主力净流出，动能衰竭"))
    
    # 3. 过热风险：换手率≥20%（注：f167字段暂不启用，待确认）
    # if profile.get("turnover_rate", 0) >= 20:
    #     risks.append(("🟠", "过热风险", f"换手率{profile['turnover_rate']}%，注意回调风险"))
    
    # 4. 涨幅预警
    if change_pct >= 75:
        risks.append(("🔴", "红旗预警", f"涨幅{change_pct:.0f}%，泡沫化风险极高"))
    elif change_pct >= 60:
        risks.append(("🟠", "黄灯预警", f"涨幅{change_pct:.0f}%，建议减仓"))
    elif change_pct >= 40:
        risks.append(("🟡", "观察预警", f"涨幅{change_pct:.0f}%，需验证基本面"))
    
    # 5. RSI超买
    rsi = tech.get("rsi14") if isinstance(tech, dict) else None
    if rsi and rsi >= 80:
        risks.append(("🟠", "RSI过热", f"RSI={rsi}，进入超买区域"))
    elif rsi and rsi >= 70:
        risks.append(("🟡", "RSI偏高", f"RSI={rsi}，接近超买区域"))
    
    return risks


def calculate_position_limit(
    market_risk: str,        # "low"/"medium"/"high"/"extreme"
    market_cap: float,         # 流通市值（亿元）
    risk_count: int,           # 风险信号数量
    stage: str                 # 生命周期阶段
) -> str:
    """计算仓位上限建议
    
    最终仓位 = 基础仓位 × 大盘风险系数 × 流通市值系数
    """
    # 基础仓位（由阶段决定）
    base_limits = {
        "爆发期": 30,
        "成熟期": 20,
        "萌芽期": 15,
        "震荡期": 10,
        "衰退期": 0,
    }
    base = base_limits.get(stage, 10)
    
    # 大盘风险系数
    market_coef = {
        "low": 1.0,
        "medium": 0.6,
        "high": 0.3,
        "extreme": 0.1,
    }.get(market_risk, 0.6)
    
    # 流通市值系数
    if market_cap < 30:
        cap_coef = 0.5
        cap_note = "<30亿，流动性风险高"
    elif market_cap < 50:
        cap_coef = 0.8
        cap_note = "30-50亿"
    else:
        cap_coef = 1.0
        cap_note = ">50亿，正常"
    
    # 禁止推荐检测
    if market_cap < 20:
        return "❌ 禁止推荐（流通市值<20亿）"
    if risk_count >= 5:
        return "❌ 清仓回避（≥5个风险信号）"
    
    final = base * market_coef * cap_coef
    
    # 风险等级调整
    if risk_count >= 3:
        final = min(final, 5)  # 最多5%
    elif risk_count >= 1:
        final = min(final, base * cap_coef * 0.5)
    
    final = max(final, 0)
    return f"建议仓位: ≤{final:.0f}%  ({cap_note})"


def build_conclusion(result: dict, market_pct: float, profile: dict = None) -> str:
    """综合所有维度输出结论性判断
    
    核心逻辑：
    1. 大盘方向（定贝塔）
    2. 资金多空博弈（定主力意图）
    3. 生命周期（定胜率）
    4. 七大风险检测（定风险）
    5. 仓位上限（定仓位）
    """
    realtime = result.get("realtime", {})
    change_pct = realtime.get("change_pct", 0)
    level2 = result.get("level2", {}).get("data", {})
    lifecycle = result.get("lifecycle", {})
    sr = result.get("support_resistance", {}).get("today", {})
    tech = result.get("technicals", {})
    
    profile = profile or {}
    lines = ["", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    lines.append("🎯 综合结论")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    verdicts = []  # 收集分项结论
    
    # ── 0. 大盘定调 ──
    market_risk = "medium"
    if market_pct < -0.5:
        verdicts.append(("🔴", "大盘弱势", "贝塔下行，整体市场偏空，选股难度大"))
        market_risk = "high"
    elif market_pct < -0.1:
        verdicts.append(("🔴", "大盘偏弱", "谨慎做多，避免重仓"))
        market_risk = "medium"
    elif market_pct > 0.5:
        verdicts.append(("🟢", "大盘强势", "顺势做多，积极参与"))
        market_risk = "low"
    else:
        verdicts.append(("⚪", "大盘震荡", "方向不明，精选个股"))
        market_risk = "medium"
    
    # ── 1. 多空博弈定意图 ──
    if level2.get("minute_data"):
        total_main = level2.get("total_main", 0)
        super_large = level2.get("total_super", 0)
        big = level2.get("total_big", 0)
        institution_net = super_large + big
        
        if total_main > 1e8 and institution_net > 0:
            verdicts.append(("🟢", "机构真金白银", "超大+大单净流入，主力真正抢筹"))
        elif total_main > 1e8 and institution_net < 0:
            verdicts.append(("🔴", "机构派发", "机构净流出+散户净买入，警惕主力出货"))
        elif institution_net > 0:
            verdicts.append(("🟢", "机构在布局", "机构主导，但规模有限"))
        elif institution_net < 0:
            verdicts.append(("🔴", "机构撤退", "大资金出逃，上涨难持续"))
        else:
            verdicts.append(("⚪", "多空均衡", "主力观望，等待信号"))
    
    # ── 2. 生命周期定阶段 ──
    stage = lifecycle.get("stage", "")
    if stage == "爆发期":
        verdicts.append(("🟢", "爆发期", "量价齐升，主升浪初期，胜率最高"))
    elif stage == "成熟期":
        verdicts.append(("🟡", "成熟期", "高位放量，注意主力高位派发风险"))
    elif stage == "衰退期":
        verdicts.append(("🔴", "衰退期", "量能萎缩，趋势向下，规避"))
    elif stage == "萌芽期":
        verdicts.append(("⚪", "萌芽期", "量能温和，仍在蓄力，等待确认信号"))
    else:
        verdicts.append(("⚪", "震荡期", "方向不明，等待趋势明朗"))
    
    # ── 3. 七大风险检测 ──
    risks = get_risk_signals(profile, change_pct, tech)
    risk_count = len(risks)
    if risks:
        lines.append("")
        lines.append("  ⚠️ 风险预警：")
        for icon, rtype, desc in risks:
            lines.append(f"    {icon} {rtype}：{desc}")
    
    # ── 4. 综合结论 ──
    positive = sum(1 for _, _, _ in [(v[0],v[1],v[2]) for v in verdicts if v[0] in ("🟢", "✅")] for _ in [None])
    # 重新统计
    pos_count = sum(1 for v in verdicts if v[0] == "🟢")
    neg_count = sum(1 for v in verdicts if v[0] == "🔴")
    # 加上风险数
    neg_count += risk_count
    
    if pos_count >= 3 and neg_count == 0:
        final_verdict = "积极关注"
        final_note = "多方信号共振，中短期胜率较高"
    elif neg_count >= 3:
        final_verdict = "保持谨慎"
        final_note = "空方信号占优，建议等待或观望"
    elif pos_count > neg_count:
        final_verdict = "轻仓试探"
        final_note = "方向偏多但需严格止损"
    elif neg_count > pos_count:
        final_verdict = "谨慎防御"
        final_note = "空方信号偏多，严格控制风险"
    else:
        final_verdict = "方向不明"
        final_note = "多空信号均衡，等待趋势明朗"
    
    lines.append("")
    for icon, tag, desc in verdicts:
        lines.append(f"  {icon} {tag}：{desc}")
    
    lines.append("")
    lines.append(f"  ╔══════════════════════════════════════╗")
    lines.append(f"  ║  【结论】{final_verdict:<20}       ║")
    lines.append(f"  ║  {final_note:<34}       ║")
    lines.append(f"  ╚══════════════════════════════════════╝")
    
    # ── 5. 仓位上限 ──
    # 流通市值（亿元，f162单位=亿元）
    market_cap_yi = profile.get("circ_market_cap", 0)  # 亿元
    position_advice = calculate_position_limit(market_risk, market_cap_yi, risk_count, stage)
    lines.append(f"")
    lines.append(f"  📊 {position_advice}")
    
    if market_cap_yi > 0:
        cap_tag = "🔴" if market_cap_yi < 30 else "🟡" if market_cap_yi < 50 else "🟢"
        lines.append(f"    {cap_tag} 流通市值: {market_cap_yi:.0f}亿")
    
    # ── 6. 基本面参考 ──
    if profile.get("pe"):
        pe = profile["pe"]
        pe_tag = "🔴" if pe >= 100 else "🟡" if pe >= 50 else "🟢"
        lines.append(f"    {pe_tag} 市盈率PE: {pe:.1f}")
    
    # 注：换手率字段f167数据异常，暂不显示
    
    # ── 7. 近5日资金流向（如果有） ──
    flow_hist = profile.get("flow_hist", [])
    if flow_hist:
        lines.append(f"")
        lines.append(f"  💰 近5日主力资金：")
        for f in flow_hist[:5]:
            arrow = "▲" if f["main_net"] > 0 else "▼"
            color = "🟢" if f["main_net"] > 0 else "🔴"
            lines.append(f"    {color} {f['date'][-5:]}  {arrow}{abs(f['main_net'])/1e8:+.2f}亿")
    
    # ── 8. 关键价位操作参考 ──
    if sr:
        current = sr.get("current", 0)
        stop_loss = sr.get("stop_loss", 0)
        resistance = sr.get("resistance1", 0)
        if current and stop_loss:
            loss_pct = (current - stop_loss) / current * 100
            lines.append(f"")
            lines.append(f"  📌 操作参考：")
            lines.append(f"    现价 {current:.2f}，若跌破 {stop_loss:.2f}（-{loss_pct:.1f}%）立即止损")
            if resistance and resistance > current:
                gain_pct = (resistance - current) / current * 100
                lines.append(f"    若突破 {resistance:.2f}（+{gain_pct:.1f}%）可考虑加仓")
            # 止盈参考
            take_profit = sr.get("take_profit", 0)
            if take_profit and take_profit > current:
                profit_pct = (take_profit - current) / current * 100
                lines.append(f"    止盈参考: {take_profit:.2f}（+{profit_pct:.1f}%）")
    
    return "\n".join(lines)


def format_technicals(tech: dict) -> str:
    """格式化技术指标输出"""
    lines = [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "📊 技术指标",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    
    rsi = tech.get("rsi14")
    if rsi is not None:
        if rsi > 70:
            rsi_icon = "🔴"
            rsi_label = "超买区"
        elif rsi < 30:
            rsi_icon = "🟢"
            rsi_label = "超卖区"
        else:
            rsi_icon = "⚪"
            rsi_label = "中性"
        lines.append(f"  RSI(14)   {rsi_icon} {rsi}  → {rsi_label}")
    
    macd = tech.get("macd")
    if macd:
        hist = macd.get("histogram", 0)
        if hist > 0:
            macd_icon = "🟢"
            macd_label = "金叉（多头）"
        elif hist < 0:
            macd_icon = "🔴"
            macd_label = "死叉（空头）"
        else:
            macd_icon = "⚪"
            macd_label = "零点"
        lines.append(f"  MACD      {macd_icon} Hist={hist:+.4f}  → {macd_label}")
        lines.append(f"            DIF={macd.get('macd'):.4f}  DEA={macd.get('signal'):.4f}")
    
    return "\n".join(lines)


def format_realtime(data: dict) -> str:
    """格式化实时行情输出"""
    change_pct = data["change_pct"]
    arrow = "▲" if change_pct > 0 else "▼" if change_pct < 0 else "—"
    sign = "+" if change_pct > 0 else ""
    color_tag = "🔴" if change_pct > 2 else "🟡" if change_pct > 0 else "🟢" if change_pct < -2 else "⚪"
    
    lines = [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🏽 实时行情 {color_tag} 现价 {data['price']:.2f}  {arrow}{sign}{change_pct:.2f}%",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"  今日区间  {data['open']:.2f} → {data['high']:.2f}（高） / {data['low']:.2f}（低）",
        f"  昨收: {data['pre_close']:.2f}    成交: {data['volume']/10000:.1f}万手  {data['amount']/100000000:.2f}亿",
    ]
    return "\n".join(lines)


def format_minute_analysis(analysis: dict, name: str = "", market_pct: float = None) -> str:
    """格式化分时分析输出（视觉化版本）"""
    if "error" in analysis:
        return f"分时分析错误: {analysis['error']}"
    
    source = analysis.get("data_source", "新浪")
    market_tag = ""
    if market_pct is not None:
        arrow = "▲" if market_pct > 0 else "▼" if market_pct < 0 else "—"
        sign = "+" if market_pct > 0 else ""
        market_tag = f" {arrow}{sign}{abs(market_pct):.2f}%"
    
    dist = analysis["distribution"]
    total_vol = analysis["total_volume"]
    
    def bar(pct: float, width: int = 20) -> str:
        filled = int(pct / 100 * width)
        empty = width - filled
        return "█" * filled + "░" * empty
    
    lines = [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🔥 分时量能{market_tag}  [源:{source}]",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"  全天成交  {total_vol:,}手  ({analysis['total_amount']/10000:.0f}万)",
        "",
        "  成交分布：",
        f"  🕘 早盘30分  {bar(dist['open_30min']['percent'])} {dist['open_30min']['percent']:5.1f}%  ({dist['open_30min']['volume']:,}手)",
        f"  🌙 上午中段  {bar(dist['mid_am']['percent'])} {dist['mid_am']['percent']:5.1f}%  ({dist['mid_am']['volume']:,}手)",
        f"  🌤️ 下午中段  {bar(dist['mid_pm']['percent'])} {dist['mid_pm']['percent']:5.1f}%  ({dist['mid_pm']['volume']:,}手)",
        f"  🌙 尾盘30分  {bar(dist['close_30min']['percent'])} {dist['close_30min']['percent']:5.1f}%  ({dist['close_30min']['volume']:,}手)",
        "",
        "  放量TOP3：",
    ]
    
    for item in analysis["top_volumes"][:3]:
        lines.append(f"    ⏰ {item['time']}  {item['price']:.2f}  {item['volume']:,}手")
    
    if analysis["signals"]:
        lines.append("")
        for signal in analysis["signals"]:
            lines.append(f"  {signal}")
    
    return "\n".join(lines)


def analyze_stock(code: str, with_minute: bool = False, with_tech: bool = False,
                  with_level2: bool = False, with_sr: bool = False,
                  with_lifecycle: bool = False,
                  realtime_cache: dict = None, market_change_pct: float = 0) -> dict:
    """分析单只股票（完整版）
    
    Args:
        market_change_pct: 大盘（上证指数）今日涨跌幅%，用于增强主力信号判断
    """
    sina_symbol = get_sina_symbol(code)
    
    # 获取实时行情（支持缓存以批量获取）
    if realtime_cache and sina_symbol in realtime_cache:
        realtime = realtime_cache[sina_symbol]
    else:
        realtime_data = fetch_realtime_sina([sina_symbol])
        realtime = realtime_data.get(sina_symbol)
    
    if not realtime:
        return {"error": f"无法获取 {code} 的行情数据"}
    
    result = {
        "code": code,
        "name": realtime["name"],
        "board": get_board_type(code),
        "realtime": realtime,
        "updated_at": datetime.now().isoformat(),
    }
    
    # 分时分析（东财主源）
    if with_minute:
        minute_data, minute_source = fetch_minute_data("sina", sina_symbol, code)
        minute_analysis = analyze_minute_volume(minute_data, market_change_pct=market_change_pct)
        minute_analysis["data_source"] = minute_source
        result["minute_analysis"] = minute_analysis
    
    # 技术指标（RSI + MACD）
    if with_tech:
        tech = {}
        daily = fetch_daily_data_em(code, days=60)
        if daily:
            closes = [d["close"] for d in daily]
            rsi14 = calculate_rsi(closes, 14)
            macd = calculate_macd(closes)
            tech = {"rsi14": rsi14, "macd": macd}
        result["technicals"] = tech
    
    # Level2 主力资金流
    if with_level2:
        flow = fetch_level2_flow(code)
        flow_signals = get_level2_signal(flow, market_change_pct)
        result["level2"] = {"data": flow, "signals": flow_signals}
    
    # 支撑/压力位
    if with_sr:
        sr = calculate_support_resistance(code)
        result["support_resistance"] = sr
    
    # 热点生命周期
    if with_lifecycle:
        lifecycle = detect_lifecycle_stage(code)
        result["lifecycle"] = lifecycle
    
    # 基本面档案（市值/PE/换手率/近5日资金流向）
    profile = fetch_stock_profile_em(code)
    result["profile"] = profile
    
    return result


def main():
    parser = argparse.ArgumentParser(description="A股实时行情与分时量能分析")
    parser.add_argument("codes", nargs="+", help="股票代码，如 600789 002446")
    parser.add_argument("--minute", "-m", action="store_true", help="包含分时量能分析")
    parser.add_argument("--tech", "-t", action="store_true", help="包含技术指标(RSI/MACD)")
    parser.add_argument("--level2", "-l", action="store_true", help="包含Level2主力资金流向分析")
    parser.add_argument("--sr", action="store_true", help="包含支撑/压力位和止损止盈参考")
    parser.add_argument("--lifecycle", action="store_true", help="包含热点生命周期阶段判断")
    parser.add_argument("--watch", "-w", action="store_true", help="监控模式：对比上次价格，有异动则告警")
    parser.add_argument("--json", "-j", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    # 监控模式下强制拉取技术指标（用于RSI告警）
    fetch_tech = args.tech or args.watch
    fetch_level2 = args.level2 or args.watch  # watch模式也带入
    
    # 获取大盘指数（用于分时分析增强）
    indices = fetch_market_indices()
    sh_pct = indices.get("s_sh000001", {}).get("change_pct", 0)
    mood, signal = get_market_context(indices)
    
    # 批量获取实时行情
    sina_symbols = [get_sina_symbol(code) for code in args.codes]
    realtime_cache = fetch_realtime_sina(sina_symbols)
    
    results = []
    for code in args.codes:
        result = analyze_stock(code, with_minute=args.minute, with_tech=fetch_tech,
                              with_level2=fetch_level2, with_sr=args.sr,
                              with_lifecycle=args.lifecycle,
                              realtime_cache=realtime_cache, market_change_pct=sh_pct)
        results.append(result)
    
    if args.json:
        output = {"market": {"indices": indices, "mood": mood, "signal": signal}, "stocks": results}
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        # 显示大盘环境
        if indices:
            # 大盘状态icon
            avg_pct = sum(v["change_pct"] for v in indices.values()) / len(indices)
            mood_icon = "🟢" if avg_pct > 0.3 else "🔴" if avg_pct < -0.3 else "⚪"
            now_str = datetime.now().strftime("%H:%M")
            
            print(f"{'═' * 56}")
            print(f"  📊 大盘环境  {mood_icon} {mood}  |  建议: {signal}  |  {now_str}")
            print(f"{'═' * 56}")
            for sym, info in indices.items():
                arrow = "▲" if info["change_pct"] > 0 else "▼" if info["change_pct"] < 0 else "—"
                sign = "+" if info["change_pct"] > 0 else ""
                color = "🟢" if info["change_pct"] > 0 else "🔴" if info["change_pct"] < 0 else "⚪"
                print(f"  {color} {info['name']:<6} {info['price']:>10.2f}  {arrow}{sign}{abs(info['change_pct']):.2f}%")
            print()
        
        for result in results:
            if "error" in result:
                print(f"错误: {result['error']}")
                continue
            
            code = result["code"]
            board = result.get("board", "主板")
            up_limit, _ = get_board_limits(code)
            
            # 监控模式
            if args.watch:
                watch_state = {
                    "code": code,
                    "name": result["name"],
                    "price": result["realtime"]["price"],
                    "change_pct": result["realtime"]["change_pct"],
                    "rsi14": result.get("technicals", {}).get("rsi14"),
                    "updated_at": datetime.now().isoformat(),
                }
                alerts = diff_watch(code, watch_state)
                if alerts:
                    print(f"{'━' * 50}")
                    print(f"  🚨 监控告警  {datetime.now().strftime('%H:%M:%S')}")
                    print(f"{'━' * 50}")
                    for alert in alerts:
                        print(f"  {alert}")
                    print(f"  现价: {watch_state['price']:.2f}  ({'+' if watch_state['change_pct']>=0 else ''}{watch_state['change_pct']:.2f}%)")
                else:
                    print(f"  ⏳ {result['name']}({code}) 平稳  {watch_state['price']:.2f}")
                save_watch_state(code, watch_state)
                continue
            
            # ── 股票报告头部 ──
            change_pct = result["realtime"]["change_pct"]
            arrow = "▲" if change_pct > 0 else "▼" if change_pct < 0 else "—"
            sign = "+" if change_pct > 0 else ""
            color = "🔴" if change_pct > 2 else "🟡" if change_pct > 0 else "🟢" if change_pct < -2 else "⚪"
            
            print(f"╔{'═' * 54}╗")
            price_str = f"{arrow}{sign}{change_pct:.2f}%"
            print(f"  🏽 {result['name']} ({code})  |  {board}  |  {price_str}")
            print(f"╚{'═' * 54}╝")
            
            print(format_realtime(result["realtime"]))
            
            if args.tech and "technicals" in result:
                print(format_technicals(result["technicals"]))
            
            # Level2 主力资金流
            if args.level2 and "level2" in result:
                l2 = result["level2"]
                print(format_level2(l2["data"], l2["signals"]))
            
            # 支撑/压力位
            if args.sr and "support_resistance" in result:
                sr = result["support_resistance"]
                if sr:
                    print(format_support_resistance(sr))
            
            # 热点生命周期
            if args.lifecycle and "lifecycle" in result:
                lc = result["lifecycle"]
                if lc:
                    print(format_lifecycle(lc))
            
            # 综合结论
            print(build_conclusion(result, sh_pct, result.get("profile", {})))
            
            print()


if __name__ == "__main__":
    main()
