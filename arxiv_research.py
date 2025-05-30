import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import re
import logging
from typing import List, Dict, Optional

# 配置日志
logger = logging.getLogger(__name__)

class ArxivResearcher:
    """ArXiv论文研究和搜索器"""
    
    def __init__(self, proxies: Optional[Dict] = None, ai_client=None):
        """
        初始化研究器
        
        Args:
            proxies: 代理设置
            ai_client: AI客户端（可选，用于查询优化）
        """
        self.base_url = "http://export.arxiv.org/api/query"
        self.proxies = proxies
        
        # AI助手（可选）
        self.ai_client = ai_client
        
        # 用户代理列表
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
    
    def generate_arxiv_query(self, topic: str) -> str:
        """
        使用大模型生成优化的arXiv搜索查询
        
        Args:
            topic: 搜索主题
            
        Returns:
            优化的查询字符串
        """
        if not self.ai_client or not hasattr(self.ai_client, 'client') or not self.ai_client.client:
            # 如果没有AI客户端，使用简单查询
            return f'all:"{topic}"'
        
        # 构建提示词
        prompt = f"""为arXiv生成精确搜索查询，要求：
1. 使用双引号包裹关键短语
2. 包含标题、摘要和分类字段
3. 返回查询格式如：'ti:"transformer" AND abs:"attention" OR cat:cs.CL'
4. 主题：{topic}
5. 只返回查询字符串，无需解释"""
        
        try:
            response = self.ai_client.client.chat.completions.create(
                model=self.ai_client.model_name,
                messages=[
                    {"role": "system", "content": "你是学术搜索专家"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0
            )
            
            query = response.choices[0].message.content.strip()
            logger.info(f"AI生成查询: {query}")
            return query
            
        except Exception as e:
            logger.warning(f"查询生成失败: {e}，使用基本查询")
            return f'all:"{topic}"'
    
    def search_papers(self, topic: str, max_results: int = 10, sort_by: str = "submittedDate", 
                     sort_order: str = "descending") -> List[Dict]:
        """
        根据主题搜索论文
        
        Args:
            topic: 搜索主题
            max_results: 最大结果数量
            sort_by: 排序方式 (submittedDate, relevance, lastUpdatedDate)
            sort_order: 排序顺序 (ascending, descending)
            
        Returns:
            论文信息列表
        """
        # 生成查询
        optimized_query = self.generate_arxiv_query(topic)
        
        # 添加请求头
        headers = {'User-Agent': self.user_agents[0]}
        
        # 构建参数
        params = {
            "search_query": optimized_query,
            "start": 0,
            "max_results": max_results * 2,  # 获取更多结果，以便过滤后仍有足够结果
            "sortBy": sort_by,
            "sortOrder": sort_order
        }
        
        try:
            logger.info(f"搜索论文: '{topic}'")
            logger.info(f"查询: {optimized_query}")
            
            # 发送请求
            response = requests.get(self.base_url, params=params, headers=headers, 
                                  timeout=30, proxies=self.proxies)
            response.raise_for_status()
            
            # 解析XML
            root = ET.fromstring(response.content)
            
            # 检查错误
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            error_elems = root.findall('.//atom:error', ns)
            if error_elems:
                error_messages = [elem.text for elem in error_elems]
                logger.error(f"API错误: {error_messages}")
                # 使用备用查询
                return self._fallback_search(topic, max_results, sort_by, sort_order)
            
            # 获取论文条目
            entries = root.findall('atom:entry', ns)
            logger.info(f"找到 {len(entries)} 个条目")
            
            # 解析论文
            papers = []
            for entry in entries:
                paper_info = self._parse_paper_entry(entry)
                if paper_info:
                    papers.append(paper_info)
                    if len(papers) >= max_results:
                        break
            
            # 检查结果
            if not papers:
                logger.info("未找到有效论文，尝试备用搜索")
                return self._fallback_search(topic, max_results, sort_by, sort_order)
            
            logger.info(f"成功获取 {len(papers)} 篇论文")
            return papers[:max_results]
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return self._fallback_search(topic, max_results, sort_by, sort_order)
    
    def _fallback_search(self, topic: str, max_results: int, sort_by: str = "submittedDate", 
                        sort_order: str = "descending") -> List[Dict]:
        """备用搜索方法 - 使用更简单的查询"""
        try:
            # 使用简单查询
            simple_query = f'all:"{topic}"'
            headers = {'User-Agent': self.user_agents[1]}
            params = {
                "search_query": simple_query,
                "start": 0,
                "max_results": max_results * 2,
                "sortBy": sort_by,
                "sortOrder": sort_order
            }
            
            logger.info(f"执行备用搜索: {simple_query}")
            response = requests.get(self.base_url, params=params, headers=headers, 
                                  timeout=30, proxies=self.proxies)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            entries = root.findall('atom:entry', {'atom': 'http://www.w3.org/2005/Atom'})
            logger.info(f"备用搜索找到 {len(entries)} 个条目")
            
            papers = []
            for entry in entries:
                paper_info = self._parse_paper_entry(entry)
                if paper_info:
                    papers.append(paper_info)
                    if len(papers) >= max_results:
                        break
            
            logger.info(f"备用搜索获取了 {len(papers)} 篇有效论文")
            return papers
            
        except Exception as e:
            logger.error(f"备用搜索失败: {e}")
            return []
    
    def _parse_paper_entry(self, entry) -> Optional[Dict]:
        """解析单篇论文的XML条目"""
        try:
            ns = {'atom': 'http://www.w3.org/2005/Atom'}

            # 提取基本信息
            title_elem = entry.find('atom:title', ns)
            summary_elem = entry.find('atom:summary', ns)
            published_elem = entry.find('atom:published', ns)
            id_elem = entry.find('atom:id', ns)

            # 检查关键字段
            if not (title_elem is not None and title_elem.text and 
                    id_elem is not None and id_elem.text):
                logger.warning("论文条目缺少标题或ID")
                return None
            
            # 提取字段内容
            title = title_elem.text.strip()
            summary = summary_elem.text.strip() if summary_elem and summary_elem.text else "摘要不可用"
            published = published_elem.text if published_elem and published_elem.text else "日期不可用"
            arxiv_url = id_elem.text
            
            # 清理文本
            title = re.sub(r'\s+', ' ', title)
            summary = re.sub(r'\s+', ' ', summary)
            
            # 提取ID
            arxiv_id = arxiv_url.split('/')[-1]
            
            # 查找PDF链接
            pdf_link = None
            for link in entry.findall('atom:link', ns):
                if link.get('type') == 'application/pdf' or link.get('title') == 'pdf':
                    pdf_link = link.get('href')
                    break
            
            # 如果没找到PDF链接
            if not pdf_link:
                logger.warning(f"论文 {arxiv_id} 没有PDF链接")
                return None
            
            # 提取作者
            authors = []
            for author in entry.findall('atom:author', ns):
                name_elem = author.find('atom:name', ns)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())
            
            if not authors:
                authors = ["作者不可用"]
            
            # 提取分类
            categories = []
            for category in entry.findall('atom:category', ns):
                term = category.get('term')
                if term:
                    categories.append(term)
            
            # 组装结果
            return {
                'id': arxiv_id,
                'title': title,
                'authors': authors,
                'summary': summary,
                'published': published,
                'pdf_link': pdf_link,
                'arxiv_url': arxiv_url,
                'categories': categories
            }
            
        except Exception as e:
            logger.error(f"解析论文条目失败: {e}")
            return None
    
    def _is_date_in_range(self, published_date: str, start_date: str, end_date: str) -> bool:
        """检查论文发布日期是否在指定范围内"""
        try:
            # ArXiv的日期格式通常是 '2024-01-15T18:30:45Z'
            if 'T' in published_date:
                pub_date = datetime.strptime(published_date[:10], '%Y-%m-%d')
            else:
                pub_date = datetime.strptime(published_date[:10], '%Y-%m-%d')
            
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            in_range = start <= pub_date <= end
            logger.debug(f"日期检查: {pub_date.strftime('%Y-%m-%d')} 在范围 [{start_date}, {end_date}] 内: {in_range}")
            return in_range
            
        except Exception as e:
            logger.warning(f"日期解析失败 '{published_date}': {e}")
            return True  # 如果日期解析失败，默认包含
    
    def search_papers_by_date_range(self, topic: str, start_date: str, end_date: str, 
                                   max_results: int = 10) -> List[Dict]:
        """
        按日期范围搜索论文
        
        Args:
            topic: 搜索主题
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            max_results: 最大结果数量
            
        Returns:
            论文信息列表
        """
        # 先获取更多结果
        all_papers = self.search_papers(topic, max_results * 3)
        
        # 按日期过滤
        filtered_papers = []
        for paper in all_papers:
            if self._is_date_in_range(paper['published'], start_date, end_date):
                filtered_papers.append(paper)
                if len(filtered_papers) >= max_results:
                    break
        
        logger.info(f"日期范围 [{start_date}, {end_date}] 内找到 {len(filtered_papers)} 篇论文")
        return filtered_papers
    
    def search_papers_by_category(self, category: str, max_results: int = 10) -> List[Dict]:
        """
        按分类搜索论文
        
        Args:
            category: 论文分类 (如 cs.AI, cs.CL, cs.LG 等)
            max_results: 最大结果数量
            
        Returns:
            论文信息列表
        """
        query = f"cat:{category}"
        headers = {'User-Agent': self.user_agents[0]}
        
        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        
        try:
            logger.info(f"按分类搜索: {category}")
            response = requests.get(self.base_url, params=params, headers=headers, 
                                  timeout=30, proxies=self.proxies)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            entries = root.findall('atom:entry', {'atom': 'http://www.w3.org/2005/Atom'})
            
            papers = []
            for entry in entries:
                paper_info = self._parse_paper_entry(entry)
                if paper_info:
                    papers.append(paper_info)
            
            logger.info(f"分类 {category} 找到 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            logger.error(f"分类搜索失败: {e}")
            return []
    
    def search_papers_by_author(self, author_name: str, max_results: int = 10) -> List[Dict]:
        """
        按作者搜索论文
        
        Args:
            author_name: 作者姓名
            max_results: 最大结果数量
            
        Returns:
            论文信息列表
        """
        query = f'au:"{author_name}"'
        headers = {'User-Agent': self.user_agents[0]}
        
        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        
        try:
            logger.info(f"按作者搜索: {author_name}")
            response = requests.get(self.base_url, params=params, headers=headers, 
                                  timeout=30, proxies=self.proxies)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            entries = root.findall('atom:entry', {'atom': 'http://www.w3.org/2005/Atom'})
            
            papers = []
            for entry in entries:
                paper_info = self._parse_paper_entry(entry)
                if paper_info:
                    papers.append(paper_info)
            
            logger.info(f"作者 {author_name} 找到 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            logger.error(f"作者搜索失败: {e}")
            return []
    
    def get_paper_statistics(self, papers: List[Dict]) -> Dict:
        """
        获取论文统计信息
        
        Args:
            papers: 论文列表
            
        Returns:
            统计信息字典
        """
        if not papers:
            return {}
        
        # 统计分类
        category_count = {}
        author_count = {}
        year_count = {}
        
        for paper in papers:
            # 分类统计
            for cat in paper.get('categories', []):
                category_count[cat] = category_count.get(cat, 0) + 1
            
            # 作者统计
            for author in paper.get('authors', []):
                if author != "作者不可用":
                    author_count[author] = author_count.get(author, 0) + 1
            
            # 年份统计
            try:
                year = paper.get('published', '')[:4]
                if year.isdigit():
                    year_count[year] = year_count.get(year, 0) + 1
            except:
                pass
        
        return {
            'total_papers': len(papers),
            'top_categories': sorted(category_count.items(), key=lambda x: x[1], reverse=True)[:10],
            'top_authors': sorted(author_count.items(), key=lambda x: x[1], reverse=True)[:10],
            'papers_by_year': sorted(year_count.items(), key=lambda x: x[0], reverse=True)
        }
