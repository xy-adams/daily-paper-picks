@echo off
echo 启动ArXiv论文定时任务调度器...
cd /d "%~dp0.."
python scripts/start_scheduler.py
pause 