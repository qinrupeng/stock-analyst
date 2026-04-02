#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盘前仲裁脚本 - 核心仲裁逻辑"""
import json
import os
import sys
import datetime

# 添加模块路径
sys.path.insert(0, r"D:\AI_Workspace\tools\premarket_cache")
sys.path.insert(0, r"D:\AI_Workspace\tools\premarket_rag")

from cache_manager import load_cache
from rag_retriever import retrieve_by_keywords, get_arbitration_hint

ARBITRATION_LOG_DIR = r"D:\AI_Workspace\tools\premarket_arbitrator"
os.makedirs(ARBITRATION_LOG_DIR, exist_ok=True)

# 置信度阈值
CONFLICT_THRESHOLD_LOW = 0.3
CONFLICT_THRESHOLD_HIGH = 0.6

def today_str():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def calculate_cache_confidence(signal, cache_data):
    """
    计算快取置信度
    基于隔夜信息的即时性和强度
    """
    if not cache_data or "data" not in cache_data:
        return 0.5, "无快取数据，默认中性"
    
    data = cache_data["data"]
    confidence = 0.5
    reasons = []
    
    # 1. 外围市场信号
    if "overseas" in data:
        overseas = data["overseas"]
        us_signals = []
        
        for key, label in [("djia", "道指"), ("ixic", "纳指"), ("sp500", "标普")]:
            if key in overseas:
                pct = overseas[key].get("change_pct", 0)
                if abs(pct) > 1.0:
                    us_signals.append(f"{label}{pct}%")
                    if pct > 0:
                        confidence += 0.05
                    else:
                        confidence -= 0.05
        
        if us_signals:
            reasons.append(f"外围: {', '.join(us_signals)}")
    
    # 2. 北向资金 - mx-data实时数据，最强信号
    nb = data.get("northbound", {})
    if nb.get("status") == "success":
        nb_total = nb.get("total", "0")
        try:
            total_val = float(nb_total)  # 单位：百万
            if total_val > 500000:  # >5000亿，强势信号
                confidence = min(1.0, confidence + 0.15)
                reasons.append(f"北向资金强势({total_val/10000:.0f}亿) +0.15")
            elif total_val > 200000:  # >2000亿，正向信号
                confidence = min(1.0, confidence + 0.08)
                reasons.append(f"北向资金({total_val/10000:.0f}亿) +0.08")
            else:  # <2000亿，温和信号
                confidence = min(1.0, confidence + 0.03)
                reasons.append(f"北向资金({total_val/10000:.0f}亿) +0.03")
        except (ValueError, TypeError):
            confidence = min(1.0, confidence + 0.05)
            reasons.append("北向资金成功 +0.05(解析异常)")
    elif nb.get("status") == "pending_browser":
        confidence -= 0.05
        reasons.append("北向资金(待抓) -0.05")
    
    # 3. 资讯新鲜度 - mx-search实时数据
    news = data.get("news", {})
    if news.get("status") == "success":
        news_count = news.get("count", 0)
        if news_count >= 10:
            confidence = min(1.0, confidence + 0.05)
            reasons.append(f"资讯丰富({news_count}条) +0.05")
        else:
            confidence = min(1.0, confidence + 0.02)
            reasons.append(f"资讯({news_count}条) +0.02")
    elif news.get("status") == "pending_browser":
        confidence -= 0.05
        reasons.append("资讯(待抓) -0.05")
    
    # 4. 昨日收盘状态（如果有快照）
    if "snapshot" in data:
        snapshot = data["snapshot"]
        if "sh000001" in snapshot:
            sh_pct = snapshot["sh000001"].get("change_pct", 0)
            if abs(sh_pct) > 1.5:
                reasons.append(f"昨日大盘{'涨' if sh_pct > 0 else '跌'}{abs(sh_pct)}%")
                # 大幅波动后次日惯性
                if sh_pct > 1.5:
                    confidence = min(1.0, confidence + 0.1)
                elif sh_pct < -1.5:
                    confidence = max(0.0, confidence - 0.1)
    
    # 5. 信号强度加成（如果传入了信号关键词）
    strong_signals = ["关税", "谈判", "停火", "制裁", "突破", "重大", "政策", "大涨", "暴跌"]
    for kw in strong_signals:
        if kw in signal:
            confidence = min(1.0, confidence + 0.05)
            reasons.append(f"强信号词:{kw}")
    
    confidence = max(0.0, min(1.0, confidence))
    return confidence, "; ".join(reasons) if reasons else "中性，无明显偏向"

def arbitration_result(signal, cache_data, rag_results):
    """
    核心仲裁逻辑
    """
    # 快取置信度
    cache_conf, cache_reasons = calculate_cache_confidence(signal, cache_data)
    
    # RAG置信度
    rag_hint = get_arbitration_hint(signal, rag_results, cache_data)
    rag_conf = rag_hint["rag_confidence"]
    
    # 冲突得分
    conflict_score = abs(cache_conf - rag_conf)
    
    # 判定
    if conflict_score < CONFLICT_THRESHOLD_LOW:
        # 差异小，取高置信度
        if cache_conf >= rag_conf:
            result = "有效"
            recommendation = f"快取置信度高({cache_conf:.2f})，信号有效，跟进"
        else:
            result = "观望"
            recommendation = f"RAG置信度高({rag_conf:.2f})，历史胜率存疑，观望"
    elif conflict_score < CONFLICT_THRESHOLD_HIGH:
        # 中等冲突，综合判断
        result = "谨慎"
        recommendation = f"快取({cache_conf:.2f})与RAG({rag_conf:.2f})冲突，谨慎操作"
    else:
        # 高度冲突
        result = "需人工复核"
        recommendation = f"高度冲突:快取({cache_conf:.2f}) vs RAG({rag_conf:.2f})，必须人工复核"
    
    # 风险警告
    warnings = []
    if rag_hint["warnings"]:
        for w in rag_hint["warnings"]:
            if "[HIGH]" in w or "[CRITICAL]" in w:
                warnings.append(w)
    
    # 严重警告必须阻断
    if any("[CRITICAL]" in w for w in warnings):
        result = "需人工复核"
        recommendation += " [CRITICAL警告，必须人工复核]"
    
    return {
        "signal": signal,
        "date": today_str(),
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cache_confidence": round(cache_conf, 3),
        "cache_reasons": cache_reasons,
        "rag_confidence": round(rag_conf, 3),
        "conflict_score": round(conflict_score, 3),
        "arbitration_result": result,
        "recommendation": recommendation,
        "warnings": warnings,
        "rag_hints": rag_hint.get("hints", []),
        "need_human_review": result == "需人工复核",
        "top_rag_matches": rag_hint.get("top_matches", [])[:3]
    }

def arbitrate_signal(signal, date_str=None):
    """
    对单个信号进行仲裁
    """
    # 加载快取数据
    if date_str:
        cache_data = load_cache(date_str)
    else:
        cache_data = load_cache()
    
    # RAG检索
    keywords = signal.replace(",", " ").replace("，", " ").split()
    knowledge_dir = r"D:\AI_Workspace\tools\premarket_rag\knowledge"
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "premarket_rag"))
    
    from rag_retriever import load_knowledge, retrieve_by_keywords
    knowledge = load_knowledge()
    rag_results = retrieve_by_keywords(keywords, knowledge)
    
    # 仲裁
    result = arbitration_result(signal, cache_data, rag_results)
    
    return result

def arbitrate_batch(signals, date_str=None):
    """
    批量仲裁多个信号
    """
    results = []
    for signal in signals:
        r = arbitrate_signal(signal, date_str)
        results.append(r)
    
    # 汇总
    summary = {
        "date": today_str(),
        "total_signals": len(signals),
        "effective": len([r for r in results if r["arbitration_result"] == "有效"]),
        "cautious": len([r for r in results if r["arbitration_result"] == "谨慎"]),
        "need_review": len([r for r in results if r["arbitration_result"] == "需人工复核"]),
        "watch": len([r for r in results if r["arbitration_result"] == "观望"]),
        "need_human_review": any(r["need_human_review"] for r in results),
        "results": results
    }
    
    return summary

def save_arbitration_log(result, date_str=None):
    """保存仲裁结果日志"""
    if date_str is None:
        date_str = today_str()
    
    # 单条日志
    log_file = os.path.join(ARBITRATION_LOG_DIR, f"{date_str}_result.json")
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return log_file

if __name__ == "__main__":
    # 用法: python premarket_arbitrator.py <信号1> [信号2] ...
    # 或: python premarket_arbitrator.py --batch <信号文件.json>
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python premarket_arbitrator.py <信号1> [信号2] ...")
        print("  python premarket_arbitrator.py --batch <信号列表.json>")
        sys.exit(1)
    
    if sys.argv[1] == "--batch":
        # 批量模式
        batch_file = sys.argv[2]
        with open(batch_file, encoding="utf-8") as f:
            signals = json.load(f)
        result = arbitrate_batch(signals)
        log_file = save_arbitration_log(result)
        
        print(f"\n{'='*50}")
        print(f"  盘前仲裁报告  {today_str()}")
        print(f"{'='*50}")
        print(f"信号总数: {result['total_signals']}")
        print(f"  有效: {result['effective']}")
        print(f"  观望: {result['watch']}")
        print(f"  谨慎: {result['cautious']}")
        print(f"  需人工复核: {result['need_review']}")
        print(f"{'='*50}")
        
        for r in result["results"]:
            icon = "✅" if r["arbitration_result"] == "有效" else "👀" if r["arbitration_result"] == "观望" else "⚠️" if r["arbitration_result"] == "谨慎" else "🔴"
            print(f"\n{icon} {r['signal']}")
            print(f"   结果: {r['arbitration_result']} | 快取:{r['cache_confidence']} RAG:{r['rag_confidence']} 冲突:{r['conflict_score']}")
            print(f"   建议: {r['recommendation']}")
            if r["warnings"]:
                for w in r["warnings"]:
                    print(f"   {w}")
        
        print(f"\n日志: {log_file}")
    
    elif sys.argv[1] == "--hotspots":
        # 热点动态仲裁模式：从热点关键词生成信号组合
        # 用法: python premarket_arbitrator.py --hotspots 创新药,SpaceX IPO,锂电
        hotspots_str = sys.argv[2] if len(sys.argv) > 2 else ""
        if not hotspots_str:
            print("错误: --hotspots 需要传入热点关键词列表")
            sys.exit(1)
        hotspots = [h.strip() for h in hotspots_str.split(",") if h.strip()]
        
        # 热点 → 信号类型 映射
        signal_types = ["关税缓和", "谈判进展", "政策利好", "外围上涨", "资金流入"]
        signals = []
        for hs in hotspots:
            for st in signal_types[:3]:  # 每个热点最多生成3个信号组合
                signals.append(f"{st}-{hs}")
        
        result = arbitrate_batch(signals)
        log_file = save_arbitration_log(result)
        
        print(f"\n{'='*50}")
        print(f"  热点动态仲裁  {today_str()}")
        print(f"{'='*50}")
        print(f"输入热点: {hotspots}")
        print(f"生成信号: {signals}")
        print(f"\n信号总数: {result['total_signals']}")
        print(f"  有效: {result['effective']}")
        print(f"  观望: {result['watch']}")
        print(f"  谨慎: {result['cautious']}")
        print(f"  需人工复核: {result['need_review']}")
        print(f"\n{'='*50}")
        for r in result["results"]:
            icon = "✅" if r["arbitration_result"] == "有效" else "👀" if r["arbitration_result"] == "观望" else "⚠️" if r["arbitration_result"] == "谨慎" else "🔴"
            print(f"\n{icon} {r['signal']}")
            print(f"   结果: {r['arbitration_result']} | 快取:{r['cache_confidence']} RAG:{r['rag_confidence']} 冲突:{r['conflict_score']}")
            print(f"   建议: {r['recommendation']}")
            if r["warnings"]:
                for w in r["warnings"]:
                    print(f"   {w}")
        print(f"\n日志: {log_file}")
    
    elif sys.argv[1] == "--test":
        # 测试模式
        test_signals = [
            "关税缓和-油运",
            "谈判进展-航运",
            "美股上涨-出口"
        ]
        result = arbitrate_batch(test_signals)
        
        print(f"\n{'='*50}")
        print(f"  仲裁脚本测试  {today_str()}")
        print(f"{'='*50}")
        
        for r in result["results"]:
            icon = "✅" if r["arbitration_result"] == "有效" else "👀" if r["arbitration_result"] == "观望" else "⚠️" if r["arbitration_result"] == "谨慎" else "🔴"
            print(f"\n{icon} {r['signal']}")
            print(f"   {r['arbitration_result']} | 快取:{r['cache_confidence']} RAG:{r['rag_confidence']}冲突:{r['conflict_score']}")
            print(f"   {r['recommendation']}")
        
        print(f"\n需要人工复核: {result['need_human_review']}")
    
    else:
        # 单信号模式
        signal = " ".join(sys.argv[1:])
        result = arbitrate_signal(signal)
        log_file = save_arbitration_log(result)
        
        print(f"\n{'='*50}")
        print(f"  盘前仲裁  {today_str()}")
        print(f"{'='*50}")
        print(f"信号: {result['signal']}")
        print(f"结果: {result['arbitration_result']}")
        print(f"快取置信度: {result['cache_confidence']} ({result['cache_reasons']})")
        print(f"RAG置信度: {result['rag_confidence']}")
        print(f"冲突得分: {result['conflict_score']}")
        print(f"建议: {result['recommendation']}")
        if result["warnings"]:
            print("警告:")
            for w in result["warnings"]:
                print(f"  {w}")
        print(f"\n需要人工复核: {result['need_human_review']}")
        print(f"日志: {log_file}")
