@echo off
chcp 65001 >nul
title Pro 1 month at 0.99
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo ============================================================
echo   Google AI Pro (5 TB)  -  1 MONTH at US$0.99
echo   SKU: g1.2tb.ai.1month_ip_95p.acq
echo   TOTAL: US$0.99  (then US$19.99/mo)
echo ============================================================
echo.

python pro0.py --account "current@device" --no-add --force --allow-paid --sku g1.2tb.ai.1month_ip_95p.acq

echo.
pause
