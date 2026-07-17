@echo off
cd /d "D:\hf_push"
set "REPO=https://github.com/lmquzi-bit/data.git"

echo ========================================
echo   Pushing to GitHub
echo ========================================

git-cmd.exe /c git remote remove origin >nul 2>&1
git-cmd.exe /c git remote add origin "%REPO%"

echo Pushing...
git-cmd.exe /c git push -u origin main

if %errorlevel%==0 (
    echo.
    echo SUCCESS! All files pushed to GitHub.
    echo.
    echo Next: go set your 3 secrets at
    echo https://github.com/lmquzi-bit/data/settings/secrets/actions
) else (
    echo.
    echo FAILED. You may need to login to GitHub first.
)

pause
