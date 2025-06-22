import os
import json
import re
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlencode
from datetime import datetime, timedelta
import random
from dataclasses import dataclass
from collections import Counter

from config.config import Config
from utils.logger import setup_logger

# 配置日志
logger = setup_logger(__name__)

@dataclass
class ArxivPaper:
    """ArXiv论文数据结构"""
    id: str
    title: str
    authors: List[str] 
    abstract: str
    categories: List[str]
    published: datetime
    updated: datetime
    pdf_url: str
    arxiv_url: str
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'categories': self.categories,
            'published': self.published.isoformat() if self.published else None,
            'updated': self.updated.isoformat() if self.updated else None,
            'pdf_url': self.pdf_url,
            'arxiv_url': self.arxiv_url,
            'pdf_link': self.pdf_url  # 兼容性字段
        }

class ArxivResearcher:
    """ArXiv研究员 - 负责搜索和分析论文"""
    
    def __init__(self, ai_client=None):
        self.base_url = Config.ARXIV_BASE_URL
        self.ai_client = ai_client
        
        # 设置请求头
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(Config.USER_AGENTS)
        })
    
    def _clean_text(self, text: str) -> str:
        """清理文本，移除多余的空白字符"""
        if not text:
            return ""
        # 移除多余的空白字符和换行
        cleaned = re.sub(r'\s+', ' ', text.strip())
        return cleaned
    
    def _parse_arxiv_response(self, xml_content: str) -> List[ArxivPaper]:
        """解析ArXiv API响应"""
        papers = []
        try:
            root = ET.fromstring(xml_content)
            
            # 定义命名空间
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            entries = root.findall('atom:entry', namespaces)
            logger.info(f"解析到 {len(entries)} 篇论文")
            
            for entry in entries:
                try:
                    # 提取基本信息
                    id_elem = entry.find('atom:id', namespaces)
                    arxiv_id = id_elem.text.split('/')[-1] if id_elem is not None else ""
                    
                    title_elem = entry.find('atom:title', namespaces)
                    title = self._clean_text(title_elem.text) if title_elem is not None else ""
                    
                    summary_elem = entry.find('atom:summary', namespaces)
                    abstract = self._clean_text(summary_elem.text) if summary_elem is not None else ""
                    
                    # 提取作者
                    authors = []
                    for author in entry.findall('atom:author', namespaces):
                        name_elem = author.find('atom:name', namespaces)
                        if name_elem is not None:
                            authors.append(self._clean_text(name_elem.text))
                    
                    # 提取分类
                    categories = []
                    for category in entry.findall('atom:category', namespaces):
                        term = category.get('term')
                        if term:
                            categories.append(term)
                    
                    # 也检查arxiv:primary_category
                    primary_cat = entry.find('arxiv:primary_category', namespaces)
                    if primary_cat is not None:
                        primary_term = primary_cat.get('term')
                        if primary_term and primary_term not in categories:
                            categories.insert(0, primary_term)
                    
                    # 提取日期
                    published_elem = entry.find('atom:published', namespaces)
                    published = None
                    if published_elem is not None:
                        try:
                            published = datetime.fromisoformat(published_elem.text.replace('Z', '+00:00'))
                        except:
                            pass
                    
                    updated_elem = entry.find('atom:updated', namespaces)
                    updated = None
                    if updated_elem is not None:
                        try:
                            updated = datetime.fromisoformat(updated_elem.text.replace('Z', '+00:00'))
                        except:
                            pass
                    
                    # 提取链接
                    pdf_url = ""
                    arxiv_url = ""
                    for link in entry.findall('atom:link', namespaces):
                        href = link.get('href', '')
                        title_attr = link.get('title', '')
                        if 'pdf' in title_attr.lower() or href.endswith('.pdf'):
                            pdf_url = href
                        elif not arxiv_url and 'arxiv.org/abs/' in href:
                            arxiv_url = href
                    
                    # 如果没有找到PDF链接，尝试构造
                    if not pdf_url and arxiv_id:
                        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                    
                    if not arxiv_url and arxiv_id:
                        arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
                    
                    # 创建论文对象
                    paper = ArxivPaper(
                        id=arxiv_id,
                        title=title,
                        authors=authors,
                        abstract=abstract,
                        categories=categories,
                        published=published,
                        updated=updated,
                        pdf_url=pdf_url,
                        arxiv_url=arxiv_url
                    )
                    
                    if paper.title and paper.abstract:  # 确保基本信息完整
                        papers.append(paper)
                        logger.debug(f"成功解析论文: {paper.title[:50]}...")
                    else:
                        logger.warning(f"跳过不完整的论文: {arxiv_id}")
                        
                except Exception as e:
                    logger.error(f"解析单篇论文时出错: {e}")
                    continue
                    
        except ET.ParseError as e:
            logger.error(f"XML解析错误: {e}")
        except Exception as e:
            logger.error(f"解析ArXiv响应时出错: {e}")
            
        logger.info(f"成功解析 {len(papers)} 篇有效论文")
        return papers
    
    def search_papers(self, 
                     query: str, 
                     max_results: int = 10,
                     sort_by: str = 'lastUpdatedDate',
                     sort_order: str = 'descending',
                     categories: List[str] = None,
                     start_date: datetime = None,
                     end_date: datetime = None) -> List[Dict]:
        """
        搜索ArXiv论文
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            sort_by: 排序方式 ('relevance', 'lastUpdatedDate', 'submittedDate')
            sort_order: 排序顺序 ('ascending', 'descending')
            categories: 指定的分类列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            论文列表
        """
        try:
            logger.info(f"开始搜索论文: {query}")
            
            # 构建搜索查询
            search_query = f"all:{query}"
            
            # 添加分类过滤
            if categories:
                cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
                search_query = f"({search_query}) AND ({cat_query})"
            
            # 添加日期过滤（注意：ArXiv API的日期格式）
            if start_date:
                start_str = start_date.strftime('%Y%m%d%H%M%S')
                search_query += f" AND submittedDate:[{start_str}*"
                
                if end_date:
                    end_str = end_date.strftime('%Y%m%d%H%M%S')
                    search_query += f" TO {end_str}]"
                else:
                    search_query += " TO *]"
            elif end_date:
                end_str = end_date.strftime('%Y%m%d%H%M%S')
                search_query += f" AND submittedDate:[* TO {end_str}]"
            
            # 构建请求参数
            params = {
                'search_query': search_query,
                'start': 0,
                'max_results': min(max_results, 100),  # API限制
                'sortBy': sort_by,
                'sortOrder': sort_order
            }
            
            # 编码URL
            url = f"{self.base_url}?{urlencode(params)}"
            logger.info(f"请求URL: {url}")
            
            # 发送请求
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 解析响应
            papers = self._parse_arxiv_response(response.text)
            
            # 转换为字典格式并添加额外字段
            results = []
            for paper in papers:
                paper_dict = paper.to_dict()
                results.append(paper_dict)
            
            logger.info(f"成功获取 {len(results)} 篇论文")
            return results
            
        except requests.RequestException as e:
            logger.error(f"网络请求失败: {e}")
            return []
        except Exception as e:
            logger.error(f"搜索论文时出错: {e}")
            return []
    
    def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict]:
        """
        根据ArXiv ID获取单篇论文信息
        
        Args:
            arxiv_id: ArXiv论文ID
            
        Returns:
            论文信息字典或None
        """
        try:
            logger.info(f"获取论文: {arxiv_id}")
            
            params = {
                'id_list': arxiv_id,
                'max_results': 1
            }
            
            url = f"{self.base_url}?{urlencode(params)}"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            papers = self._parse_arxiv_response(response.text)
            
            if papers:
                paper_dict = papers[0].to_dict()
                logger.info(f"成功获取论文: {paper_dict['title'][:50]}...")
                return paper_dict
            else:
                logger.warning(f"未找到论文: {arxiv_id}")
                return None
                
        except Exception as e:
            logger.error(f"获取论文 {arxiv_id} 时出错: {e}")
            return None
    
    def get_recent_papers(self, 
                         categories: List[str] = None,
                         days: int = 7,
                         max_results: int = 20) -> List[Dict]:
        """
        获取最近的论文
        
        Args:
            categories: 分类列表
            days: 天数
            max_results: 最大结果数
            
        Returns:
            论文列表
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 使用广泛的搜索词
        query = "*"
        
        return self.search_papers(
            query=query,
            max_results=max_results,
            categories=categories,
            start_date=start_date,
            end_date=end_date,
            sort_by='submittedDate',
            sort_order='descending'
        )
    
    def get_paper_statistics(self, papers: List[Dict]) -> Dict:
        """
        获取论文统计信息
        
        Args:
            papers: 论文列表
            
        Returns:
            统计信息
        """
        if not papers:
            return {}
        
        # 统计分类
        all_categories = []
        authors_count = []
        
        for paper in papers:
            categories = paper.get('categories', [])
            all_categories.extend(categories)
            authors_count.append(len(paper.get('authors', [])))
        
        category_counter = Counter(all_categories)
        
        stats = {
            'total_papers': len(papers),
            'top_categories': category_counter.most_common(10),
            'avg_authors': sum(authors_count) / len(authors_count) if authors_count else 0,
            'date_range': self._get_date_range(papers)
        }
        
        return stats
    
    def _get_date_range(self, papers: List[Dict]) -> Dict:
        """获取论文的日期范围"""
        dates = []
        for paper in papers:
            published = paper.get('published')
            if published:
                try:
                    if isinstance(published, str):
                        date_obj = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    else:
                        date_obj = published
                    dates.append(date_obj)
                except:
                    continue
        
        if dates:
            return {
                'earliest': min(dates).isoformat(),
                'latest': max(dates).isoformat()
            }
        return {}
    
    def filter_papers_by_keywords(self, 
                                papers: List[Dict], 
                                keywords: List[str],
                                match_type: str = 'any') -> List[Dict]:
        """
        根据关键词过滤论文
        
        Args:
            papers: 论文列表
            keywords: 关键词列表
            match_type: 匹配类型 ('any', 'all')
            
        Returns:
            过滤后的论文列表
        """
        if not keywords:
            return papers
        
        filtered_papers = []
        keywords_lower = [kw.lower() for kw in keywords]
        
        for paper in papers:
            title = paper.get('title', '').lower()
            abstract = paper.get('abstract', '').lower()
            text_content = f"{title} {abstract}"
            
            if match_type == 'all':
                if all(kw in text_content for kw in keywords_lower):
                    filtered_papers.append(paper)
            else:  # 'any'
                if any(kw in text_content for kw in keywords_lower):
                    filtered_papers.append(paper)
        
        logger.info(f"关键词过滤: {len(papers)} -> {len(filtered_papers)} 篇论文")
        return filtered_papers
    
    def rank_papers_by_relevance(self, 
                               papers: List[Dict], 
                               query: str) -> List[Dict]:
        """
        根据相关性对论文进行排序
        
        Args:
            papers: 论文列表
            query: 查询词
            
        Returns:
            排序后的论文列表
        """
        query_terms = query.lower().split()
        
        scored_papers = []
        for paper in papers:
            score = self._calculate_relevance_score(paper, query_terms)
            scored_papers.append((paper, score))
        
        # 按分数降序排序
        scored_papers.sort(key=lambda x: x[1], reverse=True)
        
        return [paper for paper, score in scored_papers]
    
    def _calculate_relevance_score(self, paper: Dict, query_terms: List[str]) -> float:
        """计算论文相关性分数"""
        title = paper.get('title', '').lower()
        abstract = paper.get('abstract', '').lower()
        
        score = 0.0
        
        for term in query_terms:
            # 标题中的匹配权重更高
            title_matches = title.count(term)
            abstract_matches = abstract.count(term)
            
            score += title_matches * 3.0  # 标题权重3倍
            score += abstract_matches * 1.0  # 摘要权重1倍
        
        return score
    
    def get_trending_topics(self, 
                          papers: List[Dict], 
                          min_frequency: int = 2) -> List[Tuple[str, int]]:
        """
        从论文中提取热门主题
        
        Args:
            papers: 论文列表
            min_frequency: 最小频率
            
        Returns:
            (主题, 频率) 的列表
        """
        # 简单的关键词提取（可以用更复杂的NLP方法）
        word_counter = Counter()
        
        # 常见停用词
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'under',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'must', 'can', 'this', 'that', 'these', 'those', 'we', 'us', 'our',
            'ours', 'you', 'your', 'yours', 'he', 'him', 'his', 'she', 'her',
            'hers', 'it', 'its', 'they', 'them', 'their', 'theirs'
        }
        
        for paper in papers:
            title = paper.get('title', '')
            # 提取标题中的关键词
            words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
            for word in words:
                if word not in stop_words:
                    word_counter[word] += 1
        
        # 过滤低频词
        trending = [(word, count) for word, count in word_counter.most_common() 
                   if count >= min_frequency]
        
        return trending[:20]  # 返回前20个 