"""
验证工具模块
提供各种数据验证功能
"""
import re
from typing import Optional

def validate_email(email: str) -> bool:
    """
    简单的邮箱地址验证
    
    Args:
        email: 邮箱地址
        
    Returns:
        是否为有效邮箱地址
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_url(url: str) -> bool:
    """
    简单的URL验证
    
    Args:
        url: URL地址
        
    Returns:
        是否为有效URL
    """
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url)) 