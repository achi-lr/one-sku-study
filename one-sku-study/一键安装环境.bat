@echo off
chcp 65001 >nul
title One-click environment setup
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo ============================================================
echo   Google AI Pro - one-click environment setup
echo ============================================================
echo   [1] check Python
echo   [2] install frida 16.5.9
echo   [3] locate adb (MuMu bundled / auto download)
echo   [4] connect emulator
echo   [5] self check
echo ============================================================
echo.

REM ---------- locate Python ----------
set "PY=python"
where python >nul 2>nul
if not errorlevel 1 goto HAVEPY
set "PY=py -3"
where py >nul 2>nul
if not errorlevel 1 goto HAVEPY

echo [ERROR] Python not found
echo.
echo   Install Python 3.10 or newer:
echo   https://www.python.org/downloads/
echo.
echo   Remember to tick "Add python.exe to PATH" during install.
echo.
pause
exit /b 1

:HAVEPY
echo [1/5] Python: %PY%
%PY% --version
echo.

if /i "%~1"=="check" goto CHECKONLY

echo [2/5] Installing. First run may take 1-2 minutes (frida download).
echo.
%PY% setup_env.py
if errorlevel 1 goto SETUPFAIL

echo.
echo ============================================================
echo   ENVIRONMENT READY
echo ============================================================
echo   Next step: double-click the bat whose name starts with 21_
echo.
echo   To only re-run the self check later, run this file with:
echo     check
echo ============================================================
echo.
pause
exit /b 0

:SETUPFAIL
echo.
echo ============================================================
echo   SETUP FAILED
echo ============================================================
echo   Common causes:
echo     1. MuMu ROOT not enabled           - see INSTALL.md image 1
echo     2. MuMu ADB not enabled            - see INSTALL.md image 2
echo     3. MuMu not running / wrong port   - start it, or use --serial
echo     4. Network blocked frida download  - retry on another network
echo     5. Play Store / Google One missing - see INSTALL.md image 3
echo.
pause
exit /b 1

:CHECKONLY
echo [check mode] environment only, no install
echo.
%PY% pro0.py --check
echo.
pause
exit /b 0
