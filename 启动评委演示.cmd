@echo off
cd /d "%~dp0"
set "GUIDE_DATA_DIR=%~dp0.runtime-jury-demo"
python -X utf8 -S run.py --port 8783
pause
