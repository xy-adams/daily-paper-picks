import os
import time
from pathlib import Path
from typing import Dict, Optional, List
import openai
from dotenv import load_dotenv

from datetime import datetime

from config.config import Config
from utils.logger import setup_logger
from utils.email_sender import send_email
from templates.prompts import PromptTemplates

# LangSmith 监控
try:
    from langsmith import traceable
    from langsmith.client import Client as LangSmithClient
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    logger = setup_logger(__name__)
    logger.warning("LangSmith未安装，将跳过监控功能")

# 加载环境变量
load_dotenv()

# 配置日志
logger = setup_logger(__name__)

class ArxivSummaryGenerator:
    """ArXiv论文总结生成器"""
    
    def __init__(self):
        # 初始化OpenAI客户端
        if Config.has_ai_config():
            self.client = openai.OpenAI(
                api_key=Config.MODEL_API_KEY,
                base_url=Config.MODEL_BASE_URL,
                timeout=Config.AI_REQUEST_TIMEOUT
            )
            self.model_name = Config.MODEL_NAME
        else:
            self.client = None
            logger.warning("未设置API密钥，将跳过AI总结功能")
        
        # 初始化LangSmith监控
        self.langsmith_client = None
        if LANGSMITH_AVAILABLE and Config.has_langsmith_config():
            try:
                os.environ["LANGSMITH_API_KEY"] = Config.LANGSMITH_API_KEY
                os.environ["LANGSMITH_PROJECT"] = Config.LANGSMITH_PROJECT
                os.environ["LANGSMITH_ENDPOINT"] = Config.LANGSMITH_ENDPOINT
                self.langsmith_client = LangSmithClient()
                logger.info("LangSmith监控已启用")
            except Exception as e:
                logger.warning(f"LangSmith初始化失败: {e}")
        
        self.data_dir = Path(Config.DATA_DIR)
        self.data_dir.mkdir(exist_ok=True)

    def _optimize_content(self, content: str) -> str:
        """优化内容长度，确保不超过模型限制"""
        if len(content) <= Config.MAX_CONTENT_LENGTH:
            return content
        
        # 截取前面的内容，保持完整性
        optimized = content[:Config.MAX_CONTENT_LENGTH]
        # 找到最后一个完整句子的位置
        last_period = optimized.rfind('.')
        if last_period > Config.MAX_CONTENT_LENGTH * 0.8:  # 如果句号位置合理
            optimized = optimized[:last_period + 1]
        return optimized + "\n\n[内容已截取...]"
    
    def generate_summary(self, paper: Dict, html_content: str) -> Optional[str]:
        """
        生成单篇论文总结
        
        Args:
            paper: 论文信息
            html_content: HTML内容
            
        Returns:
            完整的HTML内容或None
        """
        if not paper or not html_content:
            logger.error("没有论文需要处理")
            return None

        # 检查AI客户端
        if not self.client:
            logger.error("AI客户端未配置")
            return None

        # 使用提示词模板
        optimized_content = self._optimize_content(html_content)
        prompt = PromptTemplates.get_paper_summary_prompt(optimized_content)
        system_prompt = PromptTemplates.get_system_prompt()
        
        # 论文信息用于监控
        paper_title = paper.get('title', '未知标题')
        paper_id = paper.get('id', 'unknown')

        # 调用AI生成总结
        try:
            logger.info("开始生成AI总结...")
            
            # 如果LangSmith可用，使用装饰器进行监控
            if LANGSMITH_AVAILABLE and self.langsmith_client:
                summary_text = self._call_ai_with_monitoring(
                    system_prompt, 
                    prompt, 
                    paper_title, 
                    paper_id
                )
            else:
                summary_text = self._call_ai_without_monitoring(system_prompt, prompt)
            
            if summary_text:
                logger.info("AI总结生成成功")
            return summary_text
                
        except Exception as e:
            logger.error(f"AI总结生成失败: {e}")
            return None
    
    def _call_ai_with_monitoring(self, system_prompt: str, user_prompt: str, paper_title: str, paper_id: str) -> Optional[str]:
        """带LangSmith监控的AI调用"""
        @traceable(
            name="arxiv_paper_summary",
            metadata={
                "paper_title": paper_title,
                "paper_id": paper_id,
                "task": "paper_summary",
                "model": self.model_name
            }
        )
        def _traced_ai_call():
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=640000
            )
            return response.choices[0].message.content
        
        try:
            return _traced_ai_call()
        except Exception as e:
            logger.error(f"带监控的AI调用失败: {e}")
            raise
    
    def _call_ai_without_monitoring(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """不带监控的AI调用"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=640000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI调用失败: {e}")
            raise

    def save_summary(self, html_content: str, topic: str) -> str:
        """保存HTML总结到文件"""
        try:
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"arxiv_summary_{topic.replace(' ', '_')}_{timestamp}.html"
            filepath = self.data_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            logger.info(f"总结已保存到: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"保存总结失败: {e}")
            return ""

    def process_and_email(self, paper: Dict, html_content: str, email: str) -> bool:
        """
        处理单篇论文并发送邮件
        
        Args:
            paper: 论文信息
            html_content: HTML内容
            email: 目标邮箱
            
        Returns:
            bool: 是否成功
        """
        # 生成总结
        summary_html = self.generate_summary(paper, html_content)
        if not summary_html:
            logger.error("总结生成失败")
            return False
        
        # 保存总结
        paper_title = paper.get('title', '论文总结')
        self.save_summary(summary_html, paper_title)
        
        # 生成邮件主题
        subject = f"ArXiv论文总结 - {paper['title'][:30]}..."
        
        # 发送邮件
        success = send_email(email, summary_html, subject)
        if success:
            logger.info(f"邮件发送成功到: {email}")
        else:
            logger.error(f"邮件发送失败到: {email}")
        
        return success 