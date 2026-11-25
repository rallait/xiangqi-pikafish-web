@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 中国象棋 AI 服务

echo ==========================================
echo   中国象棋 AI 服务
echo   关闭此窗口即停止服务
echo ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未在 PATH 中找到 python。
    echo 请先安装 Python 3.8+，或把 python.exe 加入 PATH。
    echo.
    pause
    exit /b 1
)

python -u server.py

echo.
echo 服务已退出。按任意键关闭窗口。
pause >nul
