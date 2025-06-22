"""
通用工具模块
包含项目中常用的辅助函数和类
"""
import time
from functools import wraps
from typing import Callable, Any

def retry(max_attempts: int = 3, delay: float = 1.0):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 重试间隔时间（秒）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                    continue
            raise last_exception
        return wrapper
    return decorator

class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
    
    def update(self, increment: int = 1):
        """更新进度"""
        self.current += increment
        self._display_progress()
    
    def _display_progress(self):
        """显示进度"""
        if self.total == 0:
            return
        
        percentage = (self.current / self.total) * 100
        elapsed_time = time.time() - self.start_time
        
        if self.current > 0:
            estimated_total = elapsed_time / self.current * self.total
            remaining_time = estimated_total - elapsed_time
            print(f"\r{self.description}: {self.current}/{self.total} "
                  f"({percentage:.1f}%) - 剩余时间: {remaining_time:.1f}s", end="")
        else:
            print(f"\r{self.description}: {self.current}/{self.total} "
                  f"({percentage:.1f}%)", end="")
    
    def finish(self):
        """完成进度显示"""
        self.current = self.total
        self._display_progress()
        print()  # 换行 