@echo off
chcp 65001 >nul
title Pro stack +6 months (1)
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo ============================================================
echo   Google AI Pro (5 TB)  -  STACK +6 MONTHS  (step 1)
echo   Requires an ACTIVE subscription already.
echo   COST: US$0.00
echo   Run 1_ first, then 9_ and 10_ to reach 24 months.
echo ============================================================
echo.

python pro0.py --account "current@device" --no-add --force --stack --plan pro6

echo.
pause
