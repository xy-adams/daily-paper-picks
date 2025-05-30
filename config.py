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
    MODEL_BASE_URL = os.getenv('MODEL_BASE_URL') or os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    MODEL_NAME = os.getenv('MODEL_NAME', 'gpt-3.5-turbo')
    
    # 邮件配置
    RESEND_API_KEY = os.getenv('RESEND_API_KEY', 're_PwfckyA7_9KYJLYS4v5TXQdA7gFtKRtJt')
    EMAIL_FROM = "ArXiv论文助手 <onboarding@resend.dev>"
    
    # 下载配置
    MAX_DOWNLOAD_RETRIES = 2
    DOWNLOAD_TIMEOUT = 60
    RETRY_DELAY = 3
    MAX_PDF_PAGES = 20
    MAX_CONTENT_LENGTH = 40000
    
    # 数据目录
    DATA_DIR = "./data"
    
    # 代理配置
    HTTP_PROXY = os.getenv('HTTP_PROXY')
    HTTPS_PROXY = os.getenv('HTTPS_PROXY')
    
    # 用户代理列表
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
    
    @classmethod
    def get_proxies(cls) -> Optional[Dict[str, str]]:
        """获取代理配置"""
        proxies = {}
        if cls.HTTP_PROXY:
            proxies['http'] = cls.HTTP_PROXY
        if cls.HTTPS_PROXY:
            proxies['https'] = cls.HTTPS_PROXY
        return proxies if proxies else None
    
    @classmethod
    def has_ai_config(cls) -> bool:
        """检查是否配置了AI相关参数"""
        return bool(cls.MODEL_API_KEY)
    
    @classmethod
    def validate_config(cls) -> Dict[str, bool]:
        """验证配置完整性"""
        return {
            'ai_configured': cls.has_ai_config(),
            'proxy_configured': bool(cls.get_proxies()),
            'email_configured': bool(cls.RESEND_API_KEY)
        } 