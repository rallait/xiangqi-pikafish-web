@echo off
chcp 65001 >nul
title 中国象棋 · Pikafish AI（关闭本窗口即退出）
cd /d C:\chess-ai\gui-web
python server.py
if errorlevel 1 pause
