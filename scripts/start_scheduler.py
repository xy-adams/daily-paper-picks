"""
定时任务启动脚本
用于启动ArXiv论文自动抓取和总结的定时任务
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import run_scheduler

if __name__ == "__main__":
    print("启动ArXiv论文定时任务调度器...")
    run_scheduler() 