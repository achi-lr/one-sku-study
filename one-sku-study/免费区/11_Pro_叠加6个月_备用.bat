@echo off
chcp 65001 >nul
title Pro stack +6 months (spare)
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo ============================================================
echo   Google AI Pro (5 TB)  -  STACK +6 MONTHS  (spare offer)
echo   Use when 9_ / 10_ already consumed.
echo   COST: US$0.00
echo ============================================================
echo.

python pro0.py --account "current@device" --no-add --force --stack --plan pro6c

echo.
pause
