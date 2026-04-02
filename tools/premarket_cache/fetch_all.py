#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盘前快取数据收集"""
import json
import os
import sys
import datetime
import urllib.request
import urllib.error
import subprocess
import winreg

def get_user_env_var(name):
    """Read Windows User-level environment variable"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return value
    except Exception:
        return None

BASE_DIR = r"D:\AI_Workspace\tools\premarket_cache"
CACHE_DIR = os.path.join(BASE_DIR, "cache")
LOG_DIR = os.path.join(BASE_DIR, "logs")

def get_today():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def write_log(log_file, msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"{ts} {msg}"
    print(line)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def main():
    today = get_today()
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    output_file = os.path.join(CACHE_DIR, f"{today}_cache.json")
    log_file = os.path.join(LOG_DIR, f"{today}_fetch.log")

    # 清理旧日志
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("")

    write_log(log_file, "========== 盘前快取收集开始 ==========")
    write_log(log_file, f"日期: {today}")

    result = {
        "date": today,
        "fetch_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "partial",
        "data": {},
        "errors": []
    }

    # ---------- 1. 外围市场 ----------
    # 数据源: 新浪财经美股(收盘) + 新浪大宗商品期货(实时)
    write_log(log_file, "[1/4] 抓取外围市场...")
    overseas = {}
    
    # 1a. 美股指数 (昨晚收盘) - 新浪 gb_* 接口
    us_stocks_ok = False
    try:
        url = "https://hq.sinajs.cn/list=gb_dji,gb_ixic"
        req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn/", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode("gbk", errors="replace").strip()
        lines = text.split("\n")
        labels_keys = [("道指", "djia"), ("纳指", "ixic")]
        for i, line in enumerate(lines):
            if '"' not in line:
                continue
            val = line.split('"')[1]
            fields = val.split(",")
            if len(fields) > 4 and fields[0]:  # fields[0]=名称, fields[1]=价格, fields[2]=涨跌%, fields[4]=涨跌值
                overseas[labels_keys[i][1]] = {
                    "name": labels_keys[i][0],
                    "last": float(fields[1]) if fields[1] else 0.0,
                    "change_pct": float(fields[2]) if fields[2] else 0.0,
                    "source": "sina_us_closing",
                    "note": "美股隔夜收盘(北京时间次日早4-5点)"
                }
        us_stocks_ok = True
    except Exception as e:
        write_log(log_file, f"  [WARN] 美股数据抓取失败: {e}")
        result["errors"].append(f"us_stocks: {e}")
    
    # 1b. 大宗商品期货 - 仅在外盘交易时段可用(23:00-14:30北京时间)
    # 8:50AM 为窗口末尾，部分合约可能已休市，标记待Browser补抓
    try:
        url = "https://hq.sinajs.cn/list=mgb2,mcl2"
        req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn/", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode("gbk", errors="replace").strip()
        lines = text.split("\n")
        commodities_keys = [("gc", "黄金"), ("cl", "原油")]
        found_commodity = False
        for i, line in enumerate(lines):
            if '"' not in line:
                continue
            val = line.split('"')[1]
            fields = val.split(",")
            if len(fields) > 2 and fields[0]:
                curr = float(fields[0]) if fields[0] else 0.0
                prev = float(fields[2]) if fields[2] else curr
                chg_pct = ((curr - prev) / prev * 100) if prev else 0.0
                overseas[commodities_keys[i][0]] = {
                    "name": commodities_keys[i][1],
                    "last": curr,
                    "prev_close": prev,
                    "change_pct": round(chg_pct, 2),
                    "source": "sina_commodity_realtime",
                    "note": "NYMEX期货"
                }
                found_commodity = True
        if not found_commodity:
            overseas["gc"] = {"name": "黄金", "status": "unavailable", "note": "NYMEX 23:00-14:30北京时间，当前可能休市"}
            overseas["cl"] = {"name": "原油", "status": "unavailable", "note": "NYMEX 23:00-14:30北京时间，当前可能休市"}
            write_log(log_file, "  大宗: 商品期货在当前时段不可用(休市中)，建议Browser补抓")
    except Exception as e:
        write_log(log_file, f"  [WARN] 大宗商品期货抓取失败: {e}")
        overseas["gc"] = {"name": "黄金", "status": "error", "note": str(e)}
        overseas["cl"] = {"name": "原油", "status": "error", "note": str(e)}
        result["errors"].append(f"commodities: {e}")
    
    result["data"]["overseas"] = overseas
    djia_chg = overseas.get("djia", {}).get("change_pct", "N/A")
    ixic_chg = overseas.get("ixic", {}).get("change_pct", "N/A")
    gc_info = overseas.get("gc", {})
    cl_info = overseas.get("cl", {})
    gc_chg = gc_info.get("change_pct", gc_info.get("status", "N/A"))
    cl_chg = cl_info.get("change_pct", cl_info.get("status", "N/A"))
    write_log(log_file, f"  美股: 道指={djia_chg}% 纳指={ixic_chg}%")
    write_log(log_file, f"  大宗: 黄金={gc_chg} 原油={cl_chg}")

    # ---------- 2. 北向资金 (via mx-data) ----------
    write_log(log_file, "[2/4] 抓取北向资金...")
    mx_key = get_user_env_var("MX_APIKEY") or ""
    mx_script = os.path.join(os.environ.get("USERPROFILE", r"C:\Users\Administrator"), ".openclaw", "skills", "mx-data", "mx_data.py")
    
    if mx_key and os.path.exists(mx_script):
        try:
            import subprocess
            env = os.environ.copy()
            env["MX_APIKEY"] = mx_key
            cmd = [sys.executable, mx_script, "北向资金 今日流入"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env, encoding="utf-8", errors="replace")
            output = proc.stdout
            northbound_data = {"status": "success", "source": "mx_data"}
            for line in output.split("\n"):
                if "|" not in line:
                    continue
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) < 2:
                    continue
                val = parts[-1]
                if "北向资金成交总额" in line:
                    northbound_data["total"] = val
                elif "沪股通-成交总额" in line:
                    northbound_data["hgt"] = val
                elif "深股通-成交总额" in line:
                    northbound_data["sgt"] = val
            write_log(log_file, f"  北向资金: mx-data total={northbound_data.get('total', 'N/A')} hgt={northbound_data.get('hgt', 'N/A')} sgt={northbound_data.get('sgt', 'N/A')}")
            result["data"]["northbound"] = northbound_data
            write_log(log_file, f"  北向资金: mx-data成功 total={northbound_data.get('total', 'N/A')}")
        except Exception as e:
            result["data"]["northbound"] = {"status": "error", "error": str(e)}
            result["errors"].append(f"northbound_mx: {e}")
            write_log(log_file, f"  北向资金: mx-data失败 -> {e}")
    else:
        result["data"]["northbound"] = {
            "url": "https://data.eastmoney.com/hsgtcg/",
            "status": "pending_browser",
            "note": "mx-data未配置，需要Browser抓取"
        }
        write_log(log_file, "  北向资金: pending_browser (mx-data未配置)")

    # ---------- 3. 隔夜资讯 (via mx-search) ----------
    write_log(log_file, "[3/4] 抓取隔夜资讯...")
    mx_search_script = os.path.join(os.environ.get("USERPROFILE", r"C:\Users\Administrator"), ".openclaw", "skills", "mx-search", "mx_search.py")
    
    if mx_key and os.path.exists(mx_search_script):
        try:
            import subprocess
            env = os.environ.copy()
            env["MX_APIKEY"] = mx_key
            today_str = datetime.datetime.now().strftime("%Y年%m月%d日")
            cmd = [sys.executable, mx_search_script, f"{today_str} A股重要资讯"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env, encoding="utf-8", errors="replace")
            output = proc.stdout
            # 解析资讯数量和摘要
            news_count = 0
            news_summary = []
            for line in output.split("\n"):
                if line.strip().startswith("--- "):
                    news_count += 1
                elif line.strip().startswith("日期:"):
                    news_summary.append(line.strip()[:80])
            result["data"]["news"] = {
                "status": "success",
                "source": "mx_search",
                "count": news_count,
                "summary": news_summary[:3]  # 前3条摘要
            }
            write_log(log_file, f"  资讯: mx-search成功 共{news_count}条")
        except Exception as e:
            result["data"]["news"] = {"status": "error", "error": str(e)}
            result["errors"].append(f"news_mx: {e}")
            write_log(log_file, f"  资讯: mx-search失败 -> {e}")
    else:
        result["data"]["news"] = {
            "url": "https://www.eastmoney.com/",
            "status": "pending_browser",
            "note": "mx-search未配置，需要Browser抓取"
        }
        write_log(log_file, "  资讯: pending_browser (mx-search未配置)")

    # ---------- 4. 昨日收盘快照 ----------
    write_log(log_file, "[4/4] 抓取昨日收盘快照...")
    indices = {
        "sh000001": "上证指数",
        "sz399001": "深证成指",
        "sh000300": "沪深300",
        "sz399006": "创业板"
    }
    snapshot = {}
    failed = []
    for code, name in indices.items():
        try:
            url = f"https://qt.gtimg.cn/q={code}"
            req = urllib.request.Request(url, headers={"Referer": "https://gu.qq.com"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                text = resp.read().decode("gbk", errors="replace")
            fields = text.split("~")
            if len(fields) > 32:
                price = float(fields[3])
                prev_close = float(fields[4])
                change_val = price - prev_close  # 涨跌值(元) = 当前价 - 昨收
                change_pct = float(fields[32]) if fields[32] else 0.0   # 涨跌幅(%) 直接用字段值
                snapshot[code] = {
                    "name": name,
                    "price": price,
                    "prev_close": prev_close,
                    "change": round(change_val, 2),
                    "change_pct": round(change_pct, 2),
                    "volume": float(fields[6])
                }
        except Exception as e:
            failed.append(code)
            write_log(log_file, f"  [WARN] {name} 失败: {e}")

    result["data"]["snapshot"] = snapshot
    result["data"]["snapshot_fetch_failed"] = failed
    for code, data in snapshot.items():
        if not isinstance(data, dict):
            write_log(log_file, f"  [WARN] {code} 类型错误: {type(data)}")
            continue
        write_log(log_file, f"  {data['name']}: {data['change_pct']}%")

    # ---------- 清理旧文件 ----------
    write_log(log_file, "[清理] 删除5个交易日前的旧文件...")
    try:
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=5)).strftime("%Y-%m-%d")
        for fname in os.listdir(CACHE_DIR):
            if fname.endswith("_cache.json"):
                date_part = fname.replace("_cache.json", "")
                if date_part < cutoff:
                    os.remove(os.path.join(CACHE_DIR, fname))
                    write_log(log_file, f"  删除: {fname}")
        write_log(log_file, "  清理完成")
    except Exception as e:
        write_log(log_file, f"  [WARN] 清理失败: {e}")

    # ---------- 结果判定 ----------
    pending_count = 0
    nb = result["data"].get("northbound", {})
    news = result["data"].get("news", {})
    if nb.get("status") == "pending_browser":
        pending_count += 1
    if news.get("status") == "pending_browser":
        pending_count += 1

    total_issues = len(result["errors"]) + pending_count
    if total_issues == 0:
        result["status"] = "success"
    elif total_issues < 3:
        result["status"] = "partial"
    else:
        result["status"] = "failed"

    if nb.get("status") == "pending_browser":
        result["errors"].append("northbound: pending_browser")
    if news.get("status") == "pending_browser":
        result["errors"].append("news: pending_browser")

    # ---------- 写入JSON ----------
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    write_log(log_file, f"写入: {output_file}")
    write_log(log_file, f"状态: {result['status']}")
    write_log(log_file, f"错误数: {len(result['errors'])}")
    write_log(log_file, "========== 盘前快取收集完成 ==========")

    return 0

if __name__ == "__main__":
    sys.exit(main())
