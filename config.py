"""
配置管理模块
集中管理所有配置项，提高代码的可维护性
"""
import os
from typing import Dict, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """项目配置类"""
    
    # ArXiv API 配置
    ARXIV_BASE_URL = "http://export.arxiv.org/api/query"
    
    # AI 模型配置
    MODEL_API_KEY = os.getenv('MODEL_API_KEY') or os.getenv('OPENAI_API_KEY')
    MODEL_BASE_URL = os.getenv('MODEL_BASE_URL') or os.getenv('OPENAI_BASE_URL')
    MODEL_NAME = os.getenv('MODEL_NAME')
    
    # 邮件配置
    RESEND_API_KEY = os.getenv('RESEND_API_KEY')
    EMAIL_FROM = os.getenv('EMAIL_FROM')
    
    # 定时任务配置
    SCHEDULED_TIME = os.getenv('SCHEDULED_TIME', '07:00')  # 默认早上7点
    
    # 下载配置
    MAX_DOWNLOAD_RETRIES = 2
    DOWNLOAD_TIMEOUT = 60
    RETRY_DELAY = 3
    MAX_PDF_PAGES = 20
    MAX_CONTENT_LENGTH = 50000
    
    # 数据目录
    DATA_DIR = "./data"
    
    # 用户代理列表
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
    
    @classmethod
    def has_ai_config(cls) -> bool:
        """检查是否配置了AI相关参数"""
        return bool(cls.MODEL_API_KEY)
    
    @classmethod
    def has_email_config(cls) -> bool:
        """检查是否配置了邮件相关参数"""
        return bool(cls.RESEND_API_KEY)
    
    @classmethod
    def validate_config(cls) -> Dict[str, bool]:
        """验证配置完整性"""
        return {
            'ai_configured': cls.has_ai_config(),
            'email_configured': cls.has_email_config()
        } 