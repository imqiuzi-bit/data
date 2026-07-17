#!/bin/bash
cd "$(dirname "$0")"

REPO="https://github.com/lmquzi-bit/data.git"

echo "========================================="
echo "  A股成交金额看板 - 一键推送 GitHub"
echo "  目标仓库: $REPO"
echo "========================================="

git remote remove origin 2>/dev/null
git remote add origin "$REPO"

echo ""
echo "[1/2] 正在推送到 GitHub ..."
if git push -u origin main 2>&1; then
  echo ""
  echo "[OK] 推送成功!"
else
  echo ""
  echo "[失败] 推送失败。可能需要登录 GitHub:"
  echo "  - 如果弹出登录窗口,请用你的 GitHub 账号登录"
  echo "  - 或先在 Git Bash 里运行: git config --global credential.helper manager-core"
  echo "  - 然后重新双击本脚本"
  read -p "按回车退出..."
  exit 1
fi

echo ""
echo "[2/2] 接下来请在 GitHub 上完成:"
echo "  1. 打开 https://github.com/lmquzi-bit/data/settings/secrets/actions"
echo "  2. 点 'New repository secret', 添加 3 个:"
echo "     HF_USERNAME = lmquzi"
echo "     HF_SPACE    = 数据"
echo "     HF_TOKEN    = 你的 HF token(在 hf.co/settings/tokens 创建)"
echo "  3. 去 Actions 标签页 -> Run workflow -> 手动跑一次"
echo ""
read -p "按回车关闭..."
