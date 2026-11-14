@echo off
cd /d "%~dp0"
set "CAMPUSMATE_PUBLIC_HOST=certify-situated-unadorned.ngrok-free.dev"
set "GUIDE_ALLOW_REMOTE_LLM=false"
set "GUIDE_DATA_DIR=%~dp0.runtime-jury-demo"
python -X utf8 -S run.py --port 8783
pause
