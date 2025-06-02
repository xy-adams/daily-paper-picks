import os
from pathlib import Path
from datetime import datetime
import time
from typing import List, Dict
from arxiv_summary import ArxivSummaryGenerator
from arxiv_process import ArxivPDFProcessor
from arxiv_research import ArxivResearcher
from config import Config
from utils import setup_logger

# 配置日志
logger = setup_logger(__name__)

class ArxivPaperCrawler:
    """ArXiv论文爬虫类 - 简化版本，整合其他模块功能"""
    
    def __init__(self):
        self.data_dir = Path(Config.DATA_DIR)
        self.data_dir.mkdir(exist_ok=True)
        
        # 保存当前会话处理的论文列表
        self.current_papers = []
        
        # 初始化组件
        self.summary_generator = ArxivSummaryGenerator()
        self.pdf_processor = ArxivPDFProcessor(data_dir=str(self.data_dir))
        self.researcher = ArxivResearcher(ai_client=self.summary_generator)
    
    def search_papers(self, topic: str, max_results: int = 10) -> List[Dict]:
        """
        搜索论文
        
        Args:
            topic: 搜索主题
            max_results: 最大结果数量
            
        Returns:
            论文信息列表
        """
        return self.researcher.search_papers(topic, max_results)
    
    def process_papers(self, topic: str, max_papers: int = 1) -> bool:
        """
        完整的论文处理流程
        
        Args:
            topic: 搜索主题
            max_papers: 最大论文数量
            
        Returns:
            bool: 处理是否成功
        """
        logger.info("开始论文爬取和总结流程")
        logger.info("将下载论文PDF并生成AI总结")
        
        # 搜索论文
        papers = self.search_papers(topic, max_papers)
        
        if not papers:
            logger.error("未找到符合条件的论文")
            return False
            
        # 保存当前会话的论文列表
        self.current_papers = papers
        
        # 统计计数
        success_count = 0
        summary_count = 0
        
        # 处理每篇论文
        for i, paper in enumerate(papers, 1):
            paper_title = paper['title'][:50] + ('...' if len(paper['title']) > 50 else '')
            logger.info(f"处理论文 {i}/{len(papers)}: {paper_title}")
            
            try:
                # 1. 下载PDF
                success, pdf_path = self.pdf_processor.download_paper_pdf(paper)
                if not success:
                    logger.error(f"PDF下载失败: {pdf_path}")
                    continue
                
                logger.info(f"PDF已保存: {pdf_path}")
                success_count += 1
                
                # 2. 生成总结（如果可用）
                if Config.has_ai_config():
                    html_path = self.summary_generator.generate_summary(paper, pdf_path)
                    if html_path:
                        logger.info(f"总结已保存: {html_path}")
                        summary_count += 1
                else:
                    logger.info("跳过AI总结（未配置API密钥）")
                
            except Exception as e:
                logger.error(f"处理论文出错: {e}")
                continue
            
            # 短暂延迟，避免API限制
            time.sleep(1)
        
        # 输出统计
        logger.info(f"处理完成: 下载 {success_count}/{len(papers)} 篇论文")
        if Config.has_ai_config():
            logger.info(f"总结生成: {summary_count}/{success_count} 篇论文")
        
        return success_count > 0

def main():
    """主函数"""
    import sys
    
    print("=== ArXiv论文爬虫 ===")
    print("本程序将搜索ArXiv论文，下载PDF文件到./data目录")
    print("同时使用AI对论文内容进行总结，保存为HTML格式")
    print()
    
    # 检查环境变量
    config_status = Config.validate_config()
    print("配置检查:")
    print(f"- AI配置: {'✓' if config_status['ai_configured'] else '✗'}")
    print(f"- 邮件配置: {'✓' if config_status['email_configured'] else '✗'}")
    print()
    
    if not config_status['ai_configured']:
        print("警告: 未配置AI API密钥，将跳过论文总结生成")
        print("请设置 MODEL_API_KEY 环境变量以启用AI总结功能")
        print()
    
    try:
        topic = input("请输入要搜索的论文主题: ").strip()
        if not topic:
            logger.error("搜索主题不能为空")
            return
        
        max_papers_input = input("请输入要处理的最大论文数量 (默认1篇): ").strip()
        max_papers = int(max_papers_input) if max_papers_input else 1
        if max_papers <= 0 or max_papers > 10:
            logger.warning("论文数量应在1-10之间，使用默认值1")
            max_papers = 1
        
        print(f"\n开始处理主题: '{topic}'，最大论文数: {max_papers}")
        print("这可能需要一些时间，请耐心等待...\n")
        
        # 创建爬虫并开始处理
        crawler = ArxivPaperCrawler()
        success = crawler.process_papers(topic, max_papers)
        
        if success:
            print("\n论文处理完成！")
            print(f"下载的文件保存在: {crawler.data_dir}")
        else:
            print("\n论文处理失败！")
            
    except KeyboardInterrupt:
        logger.info("\n用户中断，程序退出")
    except Exception as e:
        logger.error(f"程序执行出错: {e}")

if __name__ == "__main__":
    main()