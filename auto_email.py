import resend
import logging
from config import Config
from utils import setup_logger

# 设置日志
logger = setup_logger(__name__)

# 设置API密钥
resend.api_key = Config.RESEND_API_KEY

def send_email(to_email: str, content: str, subject: str = "ArXiv论文总结") -> bool:
    """
    发送HTML邮件
    
    Args:
        to_email: 目标邮箱地址
        content: HTML格式邮件内容
        subject: 邮件主题
        
    Returns:
        bool: 发送是否成功
    """
    if not Config.has_email_config():
        logger.error("邮件配置未设置，无法发送邮件")
        return False
    
    params = {
        "from": Config.EMAIL_FROM,
        "to": [to_email],
        "subject": subject,
        "html": content
    }
    
    try:
        email = resend.Emails.send(params)
        logger.info(f"邮件发送成功: {email}")
        return True
    except Exception as e:
        logger.error(f"邮件发送失败: {e}")
        return False
