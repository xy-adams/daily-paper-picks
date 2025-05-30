import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import re
from pathlib import Path
import logging
from typing import List, Dict, Optional, Tuple
from io import BytesIO
from arxiv_summary import ArxivSummaryGenerator
from arxiv_process import ArxivPDFProcessor
from arxiv_research import ArxivResearcher

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ArxivPaperCrawler:
    """ArXiv论文爬虫类"""
    
    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"
        self.data_dir = Path("./data")
        self.data_dir.mkdir(exist_ok=True)
        
        # 保存当前会话处理的论文列表
        self.current_papers = []
        
        # 设置代理（如果环境变量中有设置）
        self.proxies = None
        http_proxy = os.getenv('HTTP_PROXY')
        https_proxy = os.getenv('HTTPS_PROXY')
        
        if http_proxy or https_proxy:
            self.proxies = {}
            if http_proxy:
                self.proxies['http'] = http_proxy
            if https_proxy:
                self.proxies['https'] = https_proxy
            logger.info(f"使用代理设置: {self.proxies}")
        
        # 初始化总结生成器
        self.summary_generator = ArxivSummaryGenerator()
        
        # 初始化PDF处理器
        self.pdf_processor = ArxivPDFProcessor(
            data_dir=str(self.data_dir),
            proxies=self.proxies
        )
        
        # 初始化论文研究器
        self.researcher = ArxivResearcher(
            proxies=self.proxies,
            ai_client=self.summary_generator
        )
    
    def search_papers(self, topic: str, max_results: int = 10) -> List[Dict]:
        """
        搜索论文 - 使用研究器模块
        
        Args:
            topic: 搜索主题
            max_results: 最大结果数量
            
        Returns:
            论文信息列表
        """
        return self.researcher.search_papers(topic, max_results)
    
    
    def process_papers(self, topic: str):
        """完整的论文处理流程"""
        logger.info("开始论文爬取和总结流程")
        logger.info("将下载论文PDF并生成AI总结")
        
        # 搜索论文
        papers = self.search_papers(topic, 1)
        
        if not papers:
            logger.error("未找到符合条件的论文")
            return
            
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
                if self.summary_generator.client:
                    # 使用总结生成器生成总结
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
        if self.summary_generator.client:
            logger.info(f"总结生成: {summary_count}/{success_count} 篇论文")

def test_arxiv_api():
    """测试ArXiv API连接和响应"""
    base_url = "http://export.arxiv.org/api/query"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # 测试简单查询
    test_queries = [
        'all:"machine learning"',
        'all:"computer vision"',
        'all:"natural language processing"',
        "cat:cs.LG",  # 机器学习分类
        "cat:cs.AI",  # 人工智能分类
    ]
    
    for query in test_queries:
        print(f"\n测试查询: {query}")
        params = {
            'search_query': query,
            'start': 0,
            'max_results': 5,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        try:
            response = requests.get(base_url, params=params, headers=headers, timeout=30)
            print(f"状态码: {response.status_code}")
            print(f"响应长度: {len(response.content)} 字节")
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
                entries = root.findall('atom:entry', namespaces)
                print(f"找到条目数: {len(entries)}")
                
                if entries:
                    # 显示第一个条目的信息
                    first_entry = entries[0]
                    title_elem = first_entry.find('atom:title', namespaces)
                    published_elem = first_entry.find('atom:published', namespaces)
                    
                    if title_elem is not None:
                        print(f"第一篇论文标题: {title_elem.text[:100]}...")
                    if published_elem is not None:
                        print(f"发布日期: {published_elem.text}")
                else:
                    print("没有找到任何条目")
                    # 打印部分响应内容用于调试
                    print("响应内容前500字符:")
                    print(response.text[:500])
            else:
                print(f"请求失败: {response.text[:200]}")
                
        except Exception as e:
            print(f"请求出错: {e}")

def main():
    """主函数"""
    import sys
    
    # 如果参数包含 test，则运行测试
    if len(sys.argv) > 1 and 'test' in sys.argv[1]:
        print("=== ArXiv API 连接测试 ===")
        test_arxiv_api()
        return
    
    print("=== ArXiv论文爬虫 ===")
    print("本程序将搜索ArXiv论文，下载PDF文件到./data目录")
    print("同时使用AI对论文内容进行总结，保存为HTML格式")
    print("下载超时时间设置为60秒，超时将自动跳过")
    print()
    
    # 检查环境变量
    api_key = os.getenv('MODEL_API_KEY') or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("警告：未设置API密钥，将无法生成论文总结")
        print("请设置MODEL_API_KEY或OPENAI_API_KEY环境变量")
        print()
    
    # 检查代理设置
    http_proxy = os.getenv('HTTP_PROXY')
    https_proxy = os.getenv('HTTPS_PROXY')
    if http_proxy or https_proxy:
        print(f"当前使用代理: HTTP={http_proxy}, HTTPS={https_proxy}")
    else:
        print("未检测到代理设置，如网络连接较慢，建议配置HTTP_PROXY和HTTPS_PROXY环境变量")
    print()
    
    try:
        # 创建爬虫实例
        crawler = ArxivPaperCrawler()
        
        # 获取用户输入
        topic = input("请输入搜索主题: ").strip()
        
        if not topic:
            print("错误：搜索主题不能为空")
            return
        
        print(f"\n开始搜索并处理主题: '{topic}'")
        print("这可能需要一些时间，请耐心等待...\n")
        
        # 开始处理
        crawler.process_papers(topic)
        
        print("\n处理完成！PDF文件和总结已保存到./data目录")
        
    except KeyboardInterrupt:
        print("\n用户中断，程序退出")
    except Exception as e:
        print(f"\n程序执行出错: {e}")
        logger.exception("程序异常")
        print("详细错误信息请查看日志")

if __name__ == "__main__":
    main()