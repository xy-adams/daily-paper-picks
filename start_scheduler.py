#!/usr/bin/env python3
"""
ArXiv论文自动总结定时任务启动脚本

该脚本将启动定时任务，每天早上7:00自动执行论文搜索和总结任务。
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

from main import run_scheduler

if __name__ == "__main__":
    print("启动ArXiv论文自动总结定时任务...")
    run_scheduler() 