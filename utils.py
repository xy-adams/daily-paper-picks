"""
通用工具模块
包含项目中常用的辅助函数
"""
import logging
import time
from functools import wraps
from pathlib import Path
from typing import Callable, Any

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    设置标准化的日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger

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

def ensure_directory(path: str) -> Path:
    """
    确保目录存在，如不存在则创建
    
    Args:
        path: 目录路径
        
    Returns:
        Path对象
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    截断文本到指定长度
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def safe_filename(filename: str) -> str:
    """
    生成安全的文件名，移除特殊字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        安全的文件名
    """
    import re
    # 移除或替换不安全的字符
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除连续的下划线
    safe_name = re.sub(r'_{2,}', '_', safe_name)
    # 移除开头和结尾的下划线
    safe_name = safe_name.strip('_')
    return safe_name

def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小显示
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        格式化的大小字符串
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def validate_email(email: str) -> bool:
    """
    简单的邮箱地址验证
    
    Args:
        email: 邮箱地址
        
    Returns:
        是否为有效邮箱地址
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

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