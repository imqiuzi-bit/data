@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM Git 实际安装路径（你的电脑装在 D 盘）
set "GIT=D:\软件\Git\bin\git.exe"

if not exist "%GIT%" (
  echo 未找到 git.exe，请检查路径。
  pause
  exit /b 1
)

set "REPO=https://github.com/lmquzi-bit/data.git"

echo =========================================
echo   A股成交金额看板 - 一键推送 GitHub
echo   目标仓库: %REPO%
echo =========================================
echo.

"%GIT%" remote remove origin 2>nul
"%GIT%" remote add origin "%REPO%"

echo [1/2] 正在推送到 GitHub ...
"%GIT%" push -u origin main
if %errorlevel%==0 (
  echo.
  echo [OK] 推送成功!
  echo.
  echo [2/2] 接下来请在 GitHub 网页上设置 Secrets:
  echo   1. 打开 https://github.com/lmquzi-bit/data/settings/secrets/actions
  echo   2. 点 "New repository secret" 添加 3 个:
  echo        HF_USERNAME = lmquzi
  echo        HF_SPACE    = 数据
  echo        HF_TOKEN    = 你的 HF token（hf.co/settings/tokens 创建，需 Spaces 写权限）
  echo   3. 去 Actions 标签页 -^> Run workflow -^> 手动跑一次
  echo.
) else (
  echo.
  echo [失败] 推送未成功。可能出现登录提示，请按提示登录 GitHub。
  echo   登录后在 Git Bash 里运行: "%GIT%" push -u origin main
)
pause
