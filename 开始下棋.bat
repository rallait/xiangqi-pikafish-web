@echo off
chcp 65001 >nul
title 中国象棋 · Pikafish AI（关闭本窗口即退出）
cd /d %~dp0gui-web
where python >nul 2>nul
if errorlevel 1 (
  echo 未检测到 Python，请先安装：https://www.python.org/downloads/
  echo 安装时务必勾选 "Add python.exe to PATH"
  pause
  exit /b 1
)
python server.py
if errorlevel 1 pause
