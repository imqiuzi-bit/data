#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A 股沪深两市每日成交金额 —— 数据抓取 / 每日更新脚本
============================================================
数据口径（经核对，与主流行情软件一致）:
  - 沪市成交额 = 上证指数(1.000001) 日 K 线成交额
  - 深市成交额 = 深证综指(0.399106) 日 K 线成交额   (深证综指覆盖深交所全部上市股票)
  - 两市合计   = 沪市 + 深市

说明:
  - 上证指数 / 深证综指均为"全样本"指数，其日成交额即为对应市场全部股票的成交金额。
  - 成交金额单位: 元。脚本统一换算为“亿元”存储。
  - 数据保存为 data.json（规范文件）+ data.js（供本地 file:// 直接双击打开）。

用法:
  python update.py             # 增量更新（首次运行自动回溯全部历史）
  python update.py --force     # 强制重新抓取最近 60 天（用于修正）
  python update.py --backfill  # 重新抓取全部历史

设计要点:
  - 仅在“交易日且北京时间 >= 15:00（收盘后）”才写入“当天”数据，避免盘中半成品污染历史。
  - 多节点容错: 东方财富多个 push2his 节点轮询，自动重试 + 指数退避。
  - 纯标准库实现，无需 pip 安装任何依赖。
"""

import json
import os
import sys
import time
import datetime
from datetime import datetime as dt, timedelta
from urllib.error import URLError, HTTPError
import urllib.request as ureq

try:
    from zoneinfo import ZoneInfo
    BJ = ZoneInfo("Asia/Shanghai")
except Exception:
    # CI 环境(如 GitHub Actions)常缺 zoneinfo 数据库，用固定偏移兜底
    BJ = datetime.timezone(timedelta(hours=8))

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_JSON = os.path.join(HERE, "data.json")
DATA_JS = os.path.join(HERE, "data.js")

# 东方财富多个行情节点（轮询容错）
NODES = [
    "https://push2his.eastmoney.com",
    "https://1.push2his.eastmoney.com",
    "https://2.push2his.eastmoney.com",
    "https://3.push2his.eastmoney.com",
    "https://4.push2his.eastmoney.com",
    "https://5.push2his.eastmoney.com",
    "https://6.push2his.eastmoney.com",
    "https://7.push2his.eastmoney.com",
    "https://8.push2his.eastmoney.com",
]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
REFERER = "https://quote.eastmoney.com/"

SH_SECID = "1.000001"   # 上证指数 -> 沪市成交额
SZ_SECID = "0.399106"   # 深证综指 -> 深市成交额

SOURCE_DESC = "东方财富: 上证指数(沪市) + 深证综指(深市) 日K成交额"

# 检测是否在 GitHub Actions 等 CI 环境中运行（云 IP 易被东方财富限流/超时）
IS_CI = os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI") == "true"

# CI 环境用更激进的超时策略：快速失败，把时间留给下一轮 cron 触发
if IS_CI:
    _TIMEOUT = 10       # 单请求 10 秒超时（本地 30 秒）
    _RETRIES = 3        # 单节点重试 3 次（本地 6 次）
    _MAX_ROUNDS = 2     # 整体 2 轮（本地 5 轮）
    _CI_NODES = NODES[:4]  # 只用前 4 个节点
else:
    _TIMEOUT = 30
    _RETRIES = 6
    _MAX_ROUNDS = 5
    _CI_NODES = None     # 本地用全部节点


def bj_now():
    return dt.now(BJ)


def http_get(url, retries=None, timeout=None):
    if retries is None:
        retries = _RETRIES
    if timeout is None:
        timeout = _TIMEOUT
    last = None
    for i in range(retries):
        try:
            req = ureq.Request(url, headers={
                "User-Agent": UA,
                "Referer": REFERER,
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate",
            })
            with ureq.urlopen(req, timeout=timeout) as r:
                data = r.read()
                enc = (r.headers.get("Content-Encoding") or "").lower()
                if "gzip" in enc:
                    import gzip as _gzip
                    data = _gzip.decompress(data)
                elif "deflate" in enc:
                    import zlib as _zlib
                    data = _zlib.decompress(data)
                return data.decode("utf-8", "ignore")
        except Exception as e:
            last = e
            wait = min(2 ** i + 1, 30)
            print("  [warn] 请求失败 (%s)，%ds 后重试 (%d/%d)" % (e, wait, i + 1, retries))
            time.sleep(wait)
    raise last


def fetch_kline(secid, beg, end, max_rounds=None):
    """抓取某指数日 K 线，返回 {日期: 成交额(元)}。多节点轮询 + 整轮重试。"""
    if max_rounds is None:
        max_rounds = _MAX_ROUNDS
    nodes = _CI_NODES if IS_CI else NODES
    fields2 = "f51,f52,f53,f54,f55,f56,f57"  # date,open,close,high,low,volume,amount
    last_err = None
    for rnd in range(max_rounds):
        for node in nodes:
            url = ("%s/api/qt/stock/kline/get?secid=%s&ut=fa5fd1943c7b386f172d6893dbfba10b"
                   "&fields1=f1,f2,f3,f4,f5,f6&fields2=%s&klt=101&fqt=0&beg=%s&end=%s"
                   % (node, secid, fields2, beg, end))
            try:
                txt = http_get(url)
            except Exception as e:
                last_err = e
                continue
            try:
                obj = json.loads(txt)
            except Exception:
                last_err = "JSON 解析失败"
                continue
            klines = (obj.get("data") or {}).get("klines") or []
            out = {}
            for line in klines:
                parts = line.split(",")
                if len(parts) < 7:
                    continue
                date = parts[0]
                try:
                    amount = float(parts[6])  # 元
                except ValueError:
                    continue
                out[date] = amount
            if out:
                return out
            last_err = "空数据"
        # 本轮所有节点都失败，整轮重试（间隔递增）
        if rnd < max_rounds - 1:
            wait = 15 + rnd * 10
            print("  [warn] 第 %d/%d 轮全部节点失败 (%s)，%ds 后整轮重试..."
                  % (rnd + 1, max_rounds, last_err, wait))
            time.sleep(wait)
    # 所有轮次都失败
    raise RuntimeError("抓取 %s 失败(已重试 %d 轮): %s" % (secid, max_rounds, last_err))


def load_existing():
    if os.path.exists(DATA_JSON):
        try:
            with open(DATA_JSON, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def save(rows, updated_at):
    payload = {
        "updated_at": updated_at,
        "source": SOURCE_DESC,
        "unit": "亿元",
        "note": "沪市=上证指数日成交额; 深市=深证综指日成交额; 合计=沪+深",
        "count": len(rows),
        "data": rows,
    }
    with open(DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    js = "window.A_SHARE_TURNOVER = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"
    with open(DATA_JS, "w", encoding="utf-8") as f:
        f.write(js)
    return payload


def main():
    force = "--force" in sys.argv
    backfill = "--backfill" in sys.argv

    if IS_CI:
        print("[CI 模式] 激进超时: %ds/请求, 重试%d次, %d轮, %d个节点"
              % (_TIMEOUT, _RETRIES, _MAX_ROUNDS, len(_CI_NODES)))

    existing = load_existing()
    rows = existing["data"] if (existing and "data" in existing) else []
    have = {r["date"]: r for r in rows}
    last_date = rows[-1]["date"] if rows else None

    now = bj_now()
    today_str = now.strftime("%Y-%m-%d")
    # CI 环境的 cron 触发时间已在收盘后，跳过此检查以避免时区判断偏差漏数据。
    include_today = (now.hour >= 15) or IS_CI

    if backfill:
        beg = "19901219"
        print("[backfill] 重新抓取全部历史 ...")
    elif force:
        # 重新抓取最近 60 天以修正
        d = now - timedelta(days=60)
        beg = d.strftime("%Y%m%d")
        # 删除最近 60 天已存数据，避免重复
        cutoff = d.strftime("%Y-%m-%d")
        have = {k: v for k, v in have.items() if k < cutoff}
        print("[force] 重新抓取最近 60 天 ...")
    elif last_date:
        d = dt.strptime(last_date, "%Y-%m-%d")
        beg = (d + timedelta(days=1)).strftime("%Y%m%d")
        print("[增量] 自 %s 起追加 ..." % beg)
    else:
        beg = "19901219"
        print("[首次] 回溯全部历史 ...")

    end = "20500101"

    try:
        print("抓取沪市(上证指数) ...")
        sh = fetch_kline(SH_SECID, beg, end)
        print("  获得 %d 条" % len(sh))
        print("抓取深市(深证综指) ...")
        sz = fetch_kline(SZ_SECID, beg, end)
        print("  获得 %d 条" % len(sz))
    except Exception as e:
        print("[error] 抓取失败: %s" % e)
        print("请检查网络后重试；若长时间被限流，请稍候再运行。")
        sys.exit(1)

    dates = sorted(set(sh) | set(sz))
    added = 0
    for date in dates:
        if date not in sh or date not in sz:
            continue  # 需要两市都有，保证合计准确
        if date == today_str and not include_today:
            continue  # 盘中不写入当天半成品
        sh_yi = round(sh[date] / 1e8, 2)
        sz_yi = round(sz[date] / 1e8, 2)
        have[date] = {
            "date": date,
            "sh": sh_yi,
            "sz": sz_yi,
            "total": round(sh_yi + sz_yi, 2),
        }
        added += 1

    merged = [have[k] for k in sorted(have.keys())]
    payload = save(merged, now.isoformat(timespec="seconds"))
    print("完成. 共 %d 条 (本次新增/更新 %d 条)." % (len(merged), added))
    if merged:
        last = merged[-1]
        print("最新: %s | 沪市 %.0f 亿 / 深市 %.0f 亿 / 合计 %.0f 亿"
              % (last["date"], last["sh"], last["sz"], last["total"]))


if __name__ == "__main__":
    main()
