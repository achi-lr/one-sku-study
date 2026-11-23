@echo off
chcp 65001 >nul
title Pro 12 months at 1.99
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo ============================================================
echo   Google AI Pro (5 TB)  -  12 MONTHS at US$1.99/mo
echo   SKU: g1.2tb.ai.12months_ip_90p
echo   TOTAL: US$23.88  (normal US$199.99)
echo   From month 13: US$19.99/mo
echo ============================================================
echo.

python pro0.py --account "current@device" --no-add --force --allow-paid --sku g1.2tb.ai.12months_ip_90p

echo.
pause
