import os
from typing import Dict, Tuple, Optional
from pathlib import Path
from datetime import datetime
from tavily import TavilyClient

from config.config import Config
from utils.logger import setup_logger

# 配置日志
logger = setup_logger(__name__)

class ArxivContentCrawler:
    """ArXiv论文HTML内容爬虫类 - 只负责爬取功能"""
    
    def __init__(self):
        # 初始化Tavily客户端
        tavily_api_key = os.getenv('TAVILY_API_KEY')
        self.tavily_client = TavilyClient(tavily_api_key)
        
        # 确保data目录存在
        self.data_dir = Path(Config.DATA_DIR)
        self.data_dir.mkdir(exist_ok=True)
    
    def convert_pdf_url_to_html(self, pdf_url: str) -> str:
        """
        将PDF URL转换为HTML URL
        
        Args:
            pdf_url: PDF格式的URL
            
        Returns:
            HTML格式的URL
        """
        return pdf_url.replace("/pdf/", "/html/")
    
    def save_html_content(self, content: str, paper_id: str) -> str:
        """
        保存HTML内容到文件
        
        Args:
            content: HTML内容
            paper_id: 论文ID
            
        Returns:
            保存的文件路径
        """
        try:
            # 生成文件名，使用时间戳避免重复
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # 清理paper_id中的非法字符
            safe_paper_id = "".join(c for c in paper_id if c.isalnum() or c in ".-_")
            filename = f"arxiv_raw_{safe_paper_id}_{timestamp}.html"
            filepath = self.data_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"原始HTML已保存到: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"保存HTML文件失败: {e}")
            return ""
    
    def crawl_paper_content(self, html_url: str, paper_id: str = None) -> Tuple[bool, str]:
        """
        使用Tavily爬取论文HTML内容
        
        Args:
            html_url: 论文的HTML URL
            paper_id: 论文ID（可选，用于保存文件）
            
        Returns:
            (成功标志, 爬取的内容或错误信息)
        """
        try:
            logger.info(f"开始爬取论文内容: {html_url}")
            response = self.tavily_client.extract(
                urls=html_url,
                # instructions="You only need to return one result, but you must ensure the image URL is complete.",
                # limit=2,
                # max_depth=2,
                extract_depth="advanced",
                include_images=True
            )
            
            content = str(response)
            if not content or len(content) < 100:
                logger.warning(f"爬取的内容过少: {len(content)} 字符")
                return False, "爬取的内容过少或为空"
            
            logger.info(f"成功爬取论文内容: {len(content)} 字符")
            
            # 保存原始HTML内容
            if paper_id:
                self.save_html_content(content, paper_id)
            
            return True, content
            
        except Exception as e:
            error_msg = f"爬取论文内容失败: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def crawl_paper_from_pdf_url(self, pdf_url: str, paper_id: str = None) -> Tuple[bool, str]:
        """
        从PDF URL爬取论文HTML内容
        
        Args:
            pdf_url: PDF格式的URL
            paper_id: 论文ID（可选，用于保存文件）
            
        Returns:
            (成功标志, 爬取的内容或错误信息)
        """
        html_url = self.convert_pdf_url_to_html(pdf_url)
        logger.info(f"URL转换: {pdf_url} -> {html_url}")
        return self.crawl_paper_content(html_url, paper_id)
    
    def batch_crawl_papers(self, papers: list) -> Dict[str, Tuple[bool, str]]:
        """
        批量爬取多篇论文的HTML内容
        
        Args:
            papers: 论文信息列表
            
        Returns:
            爬取结果字典 {paper_id: (success, content_or_error)}
        """
        results = {}
        success_count = 0
        
        logger.info(f"开始批量爬取 {len(papers)} 篇论文的HTML内容")
        
        for i, paper in enumerate(papers, 1):
            paper_id = paper.get('id', f'unknown_{i}')
            paper_title = paper.get('title', 'Unknown Title')[:50]
            pdf_url = paper.get('pdf_link') or paper.get('pdf_url', '')
            
            logger.info(f"爬取进度 {i}/{len(papers)}: {paper_title}")
            
            try:
                if not pdf_url:
                    error_msg = "PDF URL不可用"
                    logger.error(f"✗ {paper_id}: {error_msg}")
                    results[paper_id] = (False, error_msg)
                    continue
                
                success, result = self.crawl_paper_from_pdf_url(pdf_url, paper_id)
                results[paper_id] = (success, result)
                
                if success:
                    success_count += 1
                    logger.info(f"✓ 成功爬取: {paper_id}")
                else:
                    logger.error(f"✗ 爬取失败: {paper_id} - {result}")
                
            except Exception as e:
                error_msg = f"处理论文 {paper_id} 时出错: {e}"
                logger.error(error_msg)
                results[paper_id] = (False, error_msg)
            
            # 添加短暂延迟，避免过于频繁的请求
            if i < len(papers):  # 不是最后一个
                import time
                time.sleep(1)
        
        logger.info(f"批量爬取完成: 成功 {success_count}/{len(papers)} 篇论文")
        return results 