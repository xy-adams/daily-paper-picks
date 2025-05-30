import os
import requests
import time
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional

# 配置日志
logger = logging.getLogger(__name__)

class ArxivPDFProcessor:
    """ArXiv论文PDF处理器"""
    
    def __init__(self, data_dir: str = "./data", proxies: Optional[Dict] = None):
        """
        初始化PDF处理器
        
        Args:
            data_dir: 数据目录路径
            proxies: 代理设置
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.proxies = proxies
        
        # 多种User-Agent选项
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
    
    def download_paper_pdf(self, paper: Dict) -> Tuple[bool, str]:
        """
        从arXiv下载论文PDF文件
        
        Args:
            paper: 论文信息字典
            
        Returns:
            (成功标志, 文件路径或错误信息)
        """
        if not paper.get('pdf_link'):
            return False, "PDF链接不可用"
            
        filename = f"{paper['id']}.pdf"
        filepath = self.data_dir / filename
        
        # 检查文件是否已存在
        if filepath.exists():
            logger.info(f"PDF文件已存在: {filepath}")
            return True, str(filepath)
        
        # 设置重试参数
        max_retries = 2  # 减少重试次数
        retry_delay = 3  # 缩短重试延迟
        current_retry = 0
        
        while current_retry < max_retries:
            try:
                # 每次重试使用不同的User-Agent
                headers = {'User-Agent': self.user_agents[current_retry % len(self.user_agents)]}
                
                logger.info(f"正在下载论文PDF: {paper['id']} (尝试 {current_retry + 1}/{max_retries})")
                
                # 使用60秒超时时间
                response = requests.get(
                    paper['pdf_link'], 
                    headers=headers, 
                    timeout=60,  # 设置为60秒
                    stream=True,  # 流式下载
                    proxies=self.proxies  # 使用代理（如果有）
                )
                response.raise_for_status()
                
                # 简化内容类型检查
                content_type = response.headers.get('Content-Type', '').lower()
                is_pdf = 'application/pdf' in content_type or paper['pdf_link'].lower().endswith('.pdf')
                
                if is_pdf:
                    # 使用流式下载，防止内存占用过大
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    # 验证文件大小
                    if filepath.stat().st_size < 1000:
                        logger.warning(f"下载的PDF文件过小 ({filepath.stat().st_size} 字节)，可能不是有效PDF")
                        filepath.unlink(missing_ok=True)
                        current_retry += 1
                        time.sleep(retry_delay)
                        continue
                    
                    logger.info(f"PDF下载成功: {filepath}")
                    return True, str(filepath)
                else:
                    logger.error(f"下载的内容可能不是PDF: {content_type}")
                    current_retry += 1
                    time.sleep(retry_delay)
                    continue
                    
            except requests.exceptions.Timeout:
                logger.warning(f"下载PDF超时 (尝试 {current_retry + 1}/{max_retries})")
                current_retry += 1
                time.sleep(retry_delay)
                continue
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"下载PDF时网络错误 (尝试 {current_retry + 1}/{max_retries}): {e}")
                current_retry += 1
                time.sleep(retry_delay)
                continue
                
            except Exception as e:
                logger.error(f"下载PDF时出错: {e}")
                return False, f"下载PDF时出错: {e}"
        
        # 所有重试都失败
        error_msg = f"下载PDF失败，已重试 {max_retries} 次"
        logger.error(error_msg)
        return False, error_msg
    
    def validate_pdf_file(self, pdf_path: str) -> bool:
        """
        验证PDF文件的有效性
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            文件是否有效
        """
        try:
            file_path = Path(pdf_path)
            
            # 检查文件是否存在
            if not file_path.exists():
                logger.error(f"PDF文件不存在: {pdf_path}")
                return False
            
            # 检查文件大小
            file_size = file_path.stat().st_size
            if file_size < 1000:  # 小于1KB可能不是有效PDF
                logger.error(f"PDF文件过小: {file_size} 字节")
                return False
            
            # 检查文件头部是否为PDF格式
            with open(file_path, 'rb') as f:
                header = f.read(4)
                if not header.startswith(b'%PDF'):
                    logger.error(f"文件不是有效的PDF格式: {pdf_path}")
                    return False
            
            logger.info(f"PDF文件验证通过: {pdf_path} ({file_size} 字节)")
            return True
            
        except Exception as e:
            logger.error(f"PDF文件验证失败: {e}")
            return False
    
    def batch_download_pdfs(self, papers: list, max_concurrent: int = 3) -> Dict[str, str]:
        """
        批量下载多篇论文的PDF
        
        Args:
            papers: 论文信息列表
            max_concurrent: 最大并发下载数（暂时序列执行）
            
        Returns:
            下载结果字典 {paper_id: file_path or error_message}
        """
        results = {}
        success_count = 0
        
        logger.info(f"开始批量下载 {len(papers)} 篇论文的PDF")
        
        for i, paper in enumerate(papers, 1):
            paper_id = paper.get('id', f'unknown_{i}')
            paper_title = paper.get('title', 'Unknown Title')[:50]
            
            logger.info(f"下载进度 {i}/{len(papers)}: {paper_title}")
            
            try:
                success, result = self.download_paper_pdf(paper)
                results[paper_id] = result
                
                if success:
                    success_count += 1
                    # 验证下载的PDF
                    if self.validate_pdf_file(result):
                        logger.info(f"✓ 成功下载并验证: {paper_id}")
                    else:
                        logger.warning(f"⚠ 下载成功但验证失败: {paper_id}")
                else:
                    logger.error(f"✗ 下载失败: {paper_id} - {result}")
                
            except Exception as e:
                error_msg = f"处理论文 {paper_id} 时出错: {e}"
                logger.error(error_msg)
                results[paper_id] = error_msg
            
            # 添加短暂延迟，避免过于频繁的请求
            if i < len(papers):  # 不是最后一个
                time.sleep(1)
        
        logger.info(f"批量下载完成: 成功 {success_count}/{len(papers)} 篇论文")
        return results
    
    def get_downloaded_papers(self) -> list:
        """
        获取已下载的论文列表
        
        Returns:
            已下载的PDF文件列表
        """
        pdf_files = list(self.data_dir.glob("*.pdf"))
        logger.info(f"找到 {len(pdf_files)} 个已下载的PDF文件")
        
        return [str(f) for f in pdf_files]
    
    def cleanup_invalid_pdfs(self) -> int:
        """
        清理无效的PDF文件
        
        Returns:
            清理的文件数量
        """
        pdf_files = self.get_downloaded_papers()
        cleaned_count = 0
        
        logger.info("开始清理无效PDF文件")
        
        for pdf_path in pdf_files:
            if not self.validate_pdf_file(pdf_path):
                try:
                    Path(pdf_path).unlink()
                    logger.info(f"已删除无效PDF: {pdf_path}")
                    cleaned_count += 1
                except Exception as e:
                    logger.error(f"删除文件失败 {pdf_path}: {e}")
        
        logger.info(f"清理完成，删除了 {cleaned_count} 个无效PDF文件")
        return cleaned_count
