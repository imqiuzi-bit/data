---
title: A股沪深两市每日成交金额
emoji: 📈
colorFrom: blue
colorTo: red
sdk: static
sdk_version: static
app_file: index.html
pinned: false
---

# A股沪深两市每日成交金额

一个静态网页看板，自动展示 A 股**沪深两市每日成交金额**的柱形图，支持按 **日 / 周 / 月 / 年** 缩放，最新一天始终在图表最右侧。

- 沪市成交额 = 上证指数（1.000001）日 K 线成交额
- 深市成交额 = 深证综指（0.399106）日 K 线成交额
- 两市合计 = 沪市 + 深市
- 数据由 GitHub Actions 每日（北京时间收盘后）自动抓取并更新，无需人工干预。

## 技术
- 纯前端 ECharts 图表（已本地打包，离线可用）
- Python 脚本 `update.py` 抓取东方财富行情数据（纯标准库）
- GitHub Actions 定时任务每日自动更新 `data.json` / `data.js` 并推送至本 Space

## 本地运行
```
python update.py        # 首次运行自动回溯全部历史
python -m http.server 8000
# 浏览器打开 http://localhost:8000
```

数据仅供参考，不构成投资建议。
