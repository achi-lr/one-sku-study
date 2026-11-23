@echo off
chcp 65001 >nul
title Pro 3 months at 1.99
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo ============================================================
echo   Google AI Pro (5 TB)  -  3 MONTHS at US$1.99/mo
echo   SKU: g1.2tb.ai.3months_ip_90p.acq
echo   TOTAL: US$5.97
echo ============================================================
echo.

python pro0.py --account "current@device" --no-add --force --allow-paid --sku g1.2tb.ai.3months_ip_90p.acq

echo.
pause
