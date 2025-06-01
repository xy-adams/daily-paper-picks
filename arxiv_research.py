import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import time
import re
import logging
import math
from typing import List, Dict, Optional, Set, Tuple
from collections import Counter

# 配置日志
logger = logging.getLogger(__name__)

class ArxivResearcher:
    """ArXiv论文研究和搜索器（优化版）"""
    
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
        
        # 使用简化的停用词列表
        self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 
                             'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 
                             'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                             'will', 'would', 'could', 'should', 'may', 'might', 'can',
                             'this', 'that', 'these', 'those', 'we', 'you', 'he', 'she',
                             'it', 'they', 'them', 'their', 'our', 'your', 'his', 'her',
                             'its', 'from', 'into', 'through', 'during', 'before', 'after',
                             'above', 'below', 'up', 'down', 'out', 'off', 'over', 'under',
                             'again', 'further', 'then', 'once'])
        
        # 用户代理轮换
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        self.current_user_agent = 0
        
        # ArXiv分类映射 - 主题到相关分类的映射
        self.category_map = {
            'machine learning': ['cs.LG', 'stat.ML', 'cs.AI'],
            'deep learning': ['cs.LG', 'cs.AI', 'cs.CV', 'cs.CL'],
            'computer vision': ['cs.CV', 'cs.AI', 'cs.LG'],
            'natural language processing': ['cs.CL', 'cs.AI', 'cs.LG', 'cs.IR'],
            'nlp': ['cs.CL', 'cs.AI', 'cs.LG'],
            'transformer': ['cs.CL', 'cs.LG', 'cs.AI'],
            'attention': ['cs.CL', 'cs.LG', 'cs.AI'],
            'neural network': ['cs.LG', 'cs.AI', 'cs.NE'],
            'reinforcement learning': ['cs.LG', 'cs.AI'],
            'robotics': ['cs.RO', 'cs.AI', 'cs.LG'],
            'optimization': ['math.OC', 'cs.LG', 'stat.ML'],
            'graph neural network': ['cs.LG', 'cs.AI', 'cs.SI'],
            'recommendation': ['cs.IR', 'cs.LG', 'cs.AI'],
            'time series': ['stat.ML', 'cs.LG', 'econ.EM'],
            'generative': ['cs.LG', 'cs.AI', 'cs.CV', 'cs.CL'],
            'diffusion': ['cs.LG', 'cs.AI', 'cs.CV'],
            'language model': ['cs.CL', 'cs.AI', 'cs.LG'],
            'multimodal': ['cs.CV', 'cs.CL', 'cs.AI'],
            'self-supervised': ['cs.LG', 'cs.CV', 'cs.AI'],
            'federated learning': ['cs.LG', 'cs.DC', 'cs.AI'],
            'meta learning': ['cs.LG', 'cs.AI'],
            'few shot': ['cs.LG', 'cs.AI', 'cs.CV'],
            'zero shot': ['cs.LG', 'cs.AI', 'cs.CL'],
            'prompt': ['cs.CL', 'cs.AI', 'cs.LG'],
            'retrieval': ['cs.IR', 'cs.CL', 'cs.AI'],
            'knowledge graph': ['cs.AI', 'cs.DB', 'cs.CL'],
            'explainable ai': ['cs.AI', 'cs.LG'],
            'adversarial': ['cs.LG', 'cs.AI', 'cs.CV', 'cs.CR'],
            'privacy': ['cs.CR', 'cs.LG', 'cs.AI'],
            'quantum': ['quant-ph', 'cs.AI', 'cs.LG'],
            'blockchain': ['cs.CR', 'cs.DC', 'econ.GN'],
            'speech': ['eess.AS', 'cs.CL', 'cs.SD'],
            'audio': ['eess.AS', 'cs.SD', 'cs.AI'],
            'signal processing': ['eess.SP', 'cs.LG'],
            'biomedical': ['q-bio', 'cs.AI', 'cs.LG'],
            'medical': ['q-bio.QM', 'cs.AI', 'cs.CV'],
            'finance': ['q-fin', 'cs.LG', 'stat.ML'],
            'economics': ['econ', 'cs.GT', 'q-fin']
        }
        
        # 同义词和相关术语扩展
        self.synonym_map = {
            'transformer': ['attention', 'bert', 'gpt', 'encoder-decoder', 'self-attention'],
            'deep learning': ['neural network', 'deep neural', 'artificial neural', 'deep net'],
            'machine learning': ['ml', 'statistical learning', 'learning algorithm'],
            'computer vision': ['cv', 'image processing', 'visual recognition', 'image analysis'],
            'natural language processing': ['nlp', 'text processing', 'language understanding', 'text mining'],
            'reinforcement learning': ['rl', 'policy gradient', 'q-learning', 'actor-critic'],
            'generative': ['gan', 'vae', 'diffusion', 'autoregressive', 'generation'],
            'optimization': ['gradient descent', 'adam', 'sgd', 'training', 'learning rate'],
            'attention': ['self-attention', 'cross-attention', 'multi-head', 'attention mechanism'],
            'classification': ['categorization', 'prediction', 'recognition', 'labeling'],
            'detection': ['recognition', 'identification', 'localization', 'finding'],
            'segmentation': ['parsing', 'pixel-wise', 'semantic', 'instance'],
            'embedding': ['representation', 'encoding', 'feature', 'vector'],
            'pretraining': ['pre-training', 'self-supervised', 'unsupervised', 'pretrain'],
            'fine-tuning': ['finetuning', 'adaptation', 'transfer learning', 'finetune'],
            'multimodal': ['multi-modal', 'cross-modal', 'vision-language', 'multimedia'],
            'few-shot': ['few shot', 'k-shot', 'low-resource', 'low-data'],
            'zero-shot': ['zero shot', 'unseen', 'generalization', 'transfer'],
            'graph': ['network', 'node', 'edge', 'topology'],
            'neural': ['network', 'net', 'layer', 'neuron'],
            'convolutional': ['cnn', 'conv', 'convnet', 'convolution'],
            'recurrent': ['rnn', 'lstm', 'gru', 'sequence'],
            'adversarial': ['gan', 'attack', 'robust', 'defense']
        }
    
    def _get_next_user_agent(self) -> str:
        """获取下一个用户代理"""
        agent = self.user_agents[self.current_user_agent]
        self.current_user_agent = (self.current_user_agent + 1) % len(self.user_agents)
        return agent
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词（简化版本）"""
        text = text.lower()
        
        # 使用正则表达式提取单词
        tokens = re.findall(r'\b[a-z]{3,}\b', text)
        
        # 过滤停用词
        tokens = [token for token in tokens if token not in self.stop_words]
        
        return tokens
    
    def _expand_query_terms(self, topic: str) -> Set[str]:
        """扩展查询词汇"""
        expanded_terms = set()
        topic_lower = topic.lower()
        
        # 添加原始主题
        expanded_terms.add(topic)
        
        # 基于关键词映射扩展
        for key, synonyms in self.synonym_map.items():
            if key in topic_lower:
                expanded_terms.update(synonyms)
                expanded_terms.add(key)
        
        # 提取并添加关键词
        keywords = self._extract_keywords(topic)
        expanded_terms.update(keywords)
        
        return expanded_terms
    
    def _get_relevant_categories(self, topic: str) -> List[str]:
        """根据主题获取相关的ArXiv分类"""
        topic_lower = topic.lower()
        relevant_cats = set()
        
        for key, categories in self.category_map.items():
            if key in topic_lower:
                relevant_cats.update(categories)
        
        # 如果没有找到特定分类，返回通用AI/ML分类
        if not relevant_cats:
            relevant_cats = {'cs.AI', 'cs.LG', 'cs.CL', 'cs.CV'}
        
        return list(relevant_cats)
    
    def generate_optimized_query(self, topic: str, strategy: str = "comprehensive") -> str:
        """
        生成优化的ArXiv搜索查询
        
        Args:
            topic: 搜索主题
            strategy: 搜索策略 ('precise', 'comprehensive', 'balanced')
            
        Returns:
            优化的查询字符串
        """
        topic_clean = topic.strip()
        
        if strategy == "precise":
            # 精确搜索 - 重点在标题
            return f'ti:"{topic_clean}"'
        
        elif strategy == "comprehensive":
            # 综合搜索 - 多字段组合
            expanded_terms = self._expand_query_terms(topic_clean)
            relevant_cats = self._get_relevant_categories(topic_clean)
            
            # 构建查询组件
            query_parts = []
            
            # 标题搜索（高权重）
            if len(topic_clean.split()) <= 3:
                query_parts.append(f'ti:"{topic_clean}"')
            
            # 摘要搜索
            main_terms = list(expanded_terms)[:5]  # 限制术语数量
            abs_queries = [f'abs:"{term}"' for term in main_terms if len(term) > 3]
            if abs_queries:
                query_parts.append('(' + ' OR '.join(abs_queries) + ')')
            
            # 分类搜索
            if relevant_cats:
                cat_queries = [f'cat:{cat}' for cat in relevant_cats[:3]]
                query_parts.append('(' + ' OR '.join(cat_queries) + ')')
            
            # 组合查询
            if len(query_parts) > 1:
                return ' AND '.join(query_parts)
            elif query_parts:
                return query_parts[0]
            else:
                return f'all:"{topic_clean}"'
        
        else:  # balanced
            # 平衡搜索 - 标题+摘要
            return f'ti:"{topic_clean}" OR abs:"{topic_clean}"'
    
    def _calculate_relevance_score(self, paper: Dict, topic: str) -> float:
        """
        计算论文与主题的相关性评分
        
        Args:
            paper: 论文信息
            topic: 搜索主题
            
        Returns:
            相关性评分 (0-1)
        """
        score = 0.0
        topic_keywords = set(self._extract_keywords(topic))
        
        if not topic_keywords:
            return 0.5  # 如果无法提取关键词，返回中等分数
        
        # 标题相关性 (权重: 0.4)
        title_keywords = set(self._extract_keywords(paper.get('title', '')))
        title_overlap = len(topic_keywords.intersection(title_keywords))
        title_score = title_overlap / len(topic_keywords) if topic_keywords else 0
        score += title_score * 0.4
        
        # 摘要相关性 (权重: 0.3)
        summary_keywords = set(self._extract_keywords(paper.get('summary', '')))
        summary_overlap = len(topic_keywords.intersection(summary_keywords))
        summary_score = summary_overlap / len(topic_keywords) if topic_keywords else 0
        score += summary_score * 0.3
        
        # 分类相关性 (权重: 0.2)
        paper_cats = set(paper.get('categories', []))
        relevant_cats = set(self._get_relevant_categories(topic))
        cat_overlap = len(paper_cats.intersection(relevant_cats))
        cat_score = cat_overlap / len(relevant_cats) if relevant_cats else 0
        score += cat_score * 0.2
        
        # 时效性 (权重: 0.1) - 更新的论文得分更高
        try:
            pub_date = datetime.strptime(paper.get('published', '')[:10], '%Y-%m-%d')
            days_old = (datetime.now() - pub_date).days
            time_score = max(0, 1 - days_old / 365)  # 1年内的论文得分较高
            score += time_score * 0.1
        except:
            pass
        
        return min(score, 1.0)

    def generate_arxiv_query(self, topic: str) -> str:
        """
        使用大模型生成优化的arXiv搜索查询（兼容原接口）
        
        Args:
            topic: 搜索主题
            
        Returns:
            优化的查询字符串
        """
        if self.ai_client and hasattr(self.ai_client, 'client') and self.ai_client.client:
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
                logger.warning(f"AI查询生成失败: {e}，使用优化查询")
        
        # 使用优化的查询生成
        return self.generate_optimized_query(topic, "balanced")

    def search_papers_with_relevance(self, topic: str, max_results: int = 10, 
                                   strategy: str = "comprehensive",
                                   min_relevance: float = 0.1) -> List[Dict]:
        """
        基于相关性搜索论文（新增优化功能）
        
        Args:
            topic: 搜索主题
            max_results: 最大结果数量
            strategy: 搜索策略
            min_relevance: 最小相关性阈值
            
        Returns:
            按相关性排序的论文列表
        """
        all_papers = []
        
        # 尝试多种搜索策略
        strategies = [strategy]
        if strategy == "comprehensive":
            strategies.extend(["balanced", "precise"])
        
        for search_strategy in strategies:
            try:
                query = self.generate_optimized_query(topic, search_strategy)
                papers = self._execute_search(query, max_results * 2)
                
                # 计算相关性评分
                for paper in papers:
                    relevance_score = self._calculate_relevance_score(paper, topic)
                    paper['relevance_score'] = relevance_score
                    
                    if relevance_score >= min_relevance:
                        all_papers.append(paper)
                
                if all_papers:
                    break  # 如果找到结果就停止尝试其他策略
                    
            except Exception as e:
                logger.warning(f"搜索策略 {search_strategy} 失败: {e}")
                continue
        
        # 去重（基于ArXiv ID）
        unique_papers = {}
        for paper in all_papers:
            paper_id = paper.get('id', '')
            if paper_id not in unique_papers:
                unique_papers[paper_id] = paper
            else:
                # 保留相关性更高的版本
                if paper['relevance_score'] > unique_papers[paper_id]['relevance_score']:
                    unique_papers[paper_id] = paper
        
        # 按相关性排序
        sorted_papers = sorted(unique_papers.values(), 
                             key=lambda x: x['relevance_score'], 
                             reverse=True)
        
        logger.info(f"搜索 '{topic}' 找到 {len(sorted_papers)} 篇相关论文")
        return sorted_papers[:max_results]
    
    def _execute_search(self, query: str, max_results: int) -> List[Dict]:
        """执行搜索请求"""
        headers = {'User-Agent': self._get_next_user_agent()}
        
        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",  # 使用相关性排序
            "sortOrder": "descending"
        }
        
        logger.info(f"执行查询: {query}")
        
        try:
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
                raise Exception(f"API错误: {error_messages}")
            
            # 获取论文条目
            entries = root.findall('atom:entry', ns)
            logger.info(f"API返回 {len(entries)} 个条目")
            
            papers = []
            for entry in entries:
                paper_info = self._parse_paper_entry(entry)
                if paper_info:
                    papers.append(paper_info)
            
            return papers
            
        except Exception as e:
            logger.error(f"搜索请求失败: {e}")
            return []

    def search_papers(self, topic: str, max_results: int = 10, sort_by: str = "submittedDate", 
                     sort_order: str = "descending") -> List[Dict]:
        """
        根据主题搜索论文（优化版）
        
        Args:
            topic: 搜索主题
            max_results: 最大结果数量
            sort_by: 排序方式 (submittedDate, relevance, lastUpdatedDate)
            sort_order: 排序顺序 (ascending, descending)
            
        Returns:
            论文信息列表
        """
        # 如果指定使用相关性排序，使用优化搜索
        if sort_by == "relevance":
            return self.search_papers_with_relevance(topic, max_results)
        
        # 否则使用传统搜索，但使用优化的查询生成
        optimized_query = self.generate_arxiv_query(topic)
        
        # 添加请求头
        headers = {'User-Agent': self._get_next_user_agent()}
        
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
            headers = {'User-Agent': self._get_next_user_agent()}
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
        """解析单篇论文的XML条目（优化版）"""
        try:
            ns = {'atom': 'http://www.w3.org/2005/Atom'}

            # 提取基本信息
            title_elem = entry.find('atom:title', ns)
            summary_elem = entry.find('atom:summary', ns)
            published_elem = entry.find('atom:published', ns)
            updated_elem = entry.find('atom:updated', ns)
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
            updated = updated_elem.text if updated_elem and updated_elem.text else published
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
            
            # 如果没找到PDF链接，不返回None，而是记录警告
            if not pdf_link:
                logger.warning(f"论文 {arxiv_id} 没有PDF链接")
                # 构造PDF链接
                pdf_link = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            
            # 提取作者
            authors = []
            for author in entry.findall('atom:author', ns):
                name_elem = author.find('atom:name', ns)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())
            
            if not authors:
                authors = ["作者信息不可用"]
            
            # 提取分类
            categories = []
            for category in entry.findall('atom:category', ns):
                term = category.get('term')
                if term:
                    categories.append(term)
            
            # 额外信息提取
            # 提取DOI
            doi = None
            for link in entry.findall('atom:link', ns):
                href = link.get('href', '')
                if 'doi.org' in href:
                    doi = href.split('/')[-1]
                    break
            
            # 提取期刊信息
            journal_ref = None
            comment_elem = entry.find('atom:comment', ns)
            if comment_elem is not None and comment_elem.text:
                comment_text = comment_elem.text
                # 尝试提取期刊信息
                if any(keyword in comment_text.lower() for keyword in ['published', 'accepted', 'appeared']):
                    journal_ref = comment_text.strip()
            
            # 组装结果
            paper_data = {
                'id': arxiv_id,
                'title': title,
                'authors': authors,
                'summary': summary,
                'published': published,
                'updated': updated,
                'pdf_link': pdf_link,
                'arxiv_url': arxiv_url,
                'categories': categories,
                'doi': doi,
                'journal_ref': journal_ref,
                'relevance_score': 0.0  # 默认相关性分数
            }
            
            return paper_data
            
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
        headers = {'User-Agent': self._get_next_user_agent()}
        
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
        headers = {'User-Agent': self._get_next_user_agent()}
        
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
        获取论文统计信息（优化版）
        
        Args:
            papers: 论文列表
            
        Returns:
            统计信息字典
        """
        if not papers:
            return {}
        
        # 统计分类
        category_count = Counter()
        author_count = Counter()
        year_count = Counter()
        
        # 相关性统计
        relevance_scores = [p.get('relevance_score', 0) for p in papers]
        
        for paper in papers:
            # 分类统计
            for cat in paper.get('categories', []):
                category_count[cat] += 1
            
            # 作者统计
            for author in paper.get('authors', []):
                if author not in ["作者不可用", "作者信息不可用"]:
                    author_count[author] += 1
            
            # 年份统计
            try:
                year = paper.get('published', '')[:4]
                if year.isdigit():
                    year_count[year] += 1
            except:
                pass
        
        # 相关性分布
        high_relevance = len([s for s in relevance_scores if s > 0.5])
        medium_relevance = len([s for s in relevance_scores if 0.2 < s <= 0.5])
        low_relevance = len([s for s in relevance_scores if s <= 0.2])
        
        return {
            'total_papers': len(papers),
            'average_relevance': round(sum(relevance_scores) / len(relevance_scores), 3) if relevance_scores else 0,
            'relevance_distribution': {
                'high': high_relevance,
                'medium': medium_relevance,
                'low': low_relevance
            },
            'top_categories': category_count.most_common(10),
            'top_authors': author_count.most_common(10),
            'papers_by_year': sorted(year_count.items(), key=lambda x: x[0], reverse=True)
        }
    
    def get_paper_insights(self, papers: List[Dict], topic: str) -> Dict:
        """
        获取论文洞察分析（新增功能）
        
        Args:
            papers: 论文列表
            topic: 搜索主题
            
        Returns:
            分析洞察
        """
        if not papers:
            return {'search_topic': topic, 'total_papers': 0}
        
        # 获取基础统计
        stats = self.get_paper_statistics(papers)
        
        # 添加搜索主题信息
        stats['search_topic'] = topic
        
        # 分析主题相关性
        relevant_categories = self._get_relevant_categories(topic)
        topic_keywords = set(self._extract_keywords(topic))
        
        # 统计每篇论文的主题匹配度
        topic_matches = []
        for paper in papers:
            paper_cats = set(paper.get('categories', []))
            cat_match = len(paper_cats.intersection(set(relevant_categories)))
            
            title_keywords = set(self._extract_keywords(paper.get('title', '')))
            keyword_match = len(topic_keywords.intersection(title_keywords))
            
            topic_matches.append({
                'title': paper.get('title', ''),
                'category_match': cat_match,
                'keyword_match': keyword_match,
                'relevance_score': paper.get('relevance_score', 0)
            })
        
        # 添加主题分析
        stats['topic_analysis'] = {
            'relevant_categories': relevant_categories,
            'topic_keywords': list(topic_keywords),
            'best_matches': sorted(topic_matches, key=lambda x: x['relevance_score'], reverse=True)[:5]
        }
        
        return stats

# 创建增强版搜索器（向后兼容）
researcher = ArxivResearcher()

# 使用示例（保持原有功能）
if __name__ == "__main__":
    # 传统搜索
    papers = researcher.search_papers("transformer attention mechanism", max_results=10)
    
    # 新增相关性搜索示例
    relevant_papers = researcher.search_papers_with_relevance(
        "transformer attention mechanism", 
        max_results=10, 
        strategy="comprehensive"
    )
    
    print(f"找到 {len(relevant_papers)} 篇相关论文")
    for paper in relevant_papers[:3]:
        print(f"- {paper['title']} (相关性: {paper['relevance_score']:.3f})")
