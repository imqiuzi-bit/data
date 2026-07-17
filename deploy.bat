@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "REPO=%~1"
if "%REPO%"=="" (
  REM ====== 你的仓库地址已预填，直接回车即可 ======
  set "REPO=https://github.com/lmquzi-bit/data.git"
)
if "%REPO%"=="" (
  echo 未提供仓库地址，已取消。
  pause & exit /b 1
)

REM 设置/更新 remote 并推送
git remote remove origin >nul 2>nul
git remote add origin "%REPO%"

echo.
echo 正在推送到 GitHub (%REPO%) ...
git push -u origin main

if %errorlevel%==0 (
  echo.
  echo [OK] 代码已推送到 GitHub。
  echo.
  echo 接下来在你的 GitHub 仓库网页里完成 3 步（约 3 分钟）:
  echo   1. Settings -^> Secrets and variables -^> Actions -^> New repository secret
  echo      添加三个 secret:
  echo        HF_USERNAME = 你的 HuggingFace 用户名
  echo        HF_SPACE    = 你的 Space 名称(例如 a-share-turnover)
  echo        HF_TOKEN    = 在 hf.co/settings/tokens 生成的、有 Spaces 写权限的 token
  echo   2. 到 HuggingFace 先建一个空的 Static Space(名称与上面的 HF_SPACE 一致)
  echo   3. 在 GitHub 仓库 Actions 标签页点 "Run workflow" 手动跑一次，
  echo      会立即抓取数据并推送到你的 Space；之后每天北京 17:30 自动更新。
) else (
  echo.
  echo [失败] 推送未成功。请确认:
  echo   - 仓库地址正确，且仓库已在 GitHub 上创建(建议建空仓库)
  echo   - 本机已登录 GitHub(可用 Git Credential Manager 或 'gh auth login')
)
pause
