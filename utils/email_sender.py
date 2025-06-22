"""
邮件发送工具模块
处理论文总结的邮件发送功能
"""
import resend
import os
from typing import Optional

from config.config import Config
from utils.logger import setup_logger

# 配置日志
logger = setup_logger(__name__)

def send_email(to_email: str, html_content: str, subject: str = "ArXiv论文总结") -> bool:
    """
    发送邮件
    
    Args:
        to_email: 收件人邮箱
        html_content: HTML内容
        subject: 邮件主题
        
    Returns:
        bool: 是否发送成功
    """
    try:
        # 设置API密钥
        resend.api_key = Config.RESEND_API_KEY
        
        # 发送邮件
        response = resend.Emails.send({
            "from": Config.EMAIL_FROM or "noreply@example.com",
            "to": to_email,
            "subject": subject,
            "html": html_content
        })
        
        logger.info(f"邮件发送成功: {response}")
        return True
        
    except Exception as e:
        logger.error(f"邮件发送失败: {e}")
        return False 