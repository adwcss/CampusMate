@echo off
setlocal
cd /d "%~dp0"
python -X utf8 -I -S tools\jury_check.py
set "check_status=%errorlevel%"
if "%check_status%"=="0" (echo Review checks passed.) else (echo Review checks failed. See the output above.)
if /i not "%~1"=="--no-pause" pause
exit /b %check_status%
