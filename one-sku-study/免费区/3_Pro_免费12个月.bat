@echo off
chcp 65001 >nul
title Pro FREE 12 months
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo ============================================================
echo   Google AI Pro (5 TB)  -  FREE TRIAL 12 MONTHS
echo   SKU: g1.2tb.ai.12months_eft
echo   COST: US$0.00
echo ============================================================
echo.

python pro0.py --account "current@device" --no-add --force --sku g1.2tb.ai.12months_eft

echo.
pause
