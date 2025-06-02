import os
import time
from pathlib import Path
from typing import Dict, Optional, List
import openai
from dotenv import load_dotenv
import markdown
import html
import PyPDF2
from config import Config
from utils import setup_logger

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
                base_url=Config.MODEL_BASE_URL
            )
            self.model_name = Config.MODEL_NAME
        else:
            self.client = None
            logger.warning("未设置API密钥，将跳过AI总结功能")
        
        self.data_dir = Path(Config.DATA_DIR)
        self.data_dir.mkdir(exist_ok=True)
    
    def extract_text_from_pdf(self, pdf_path: str, current_papers: List[Dict] = None) -> str:
        """
        从PDF文件中提取文本内容
        
        Args:
            pdf_path: PDF文件路径
            current_papers: 当前论文列表，用于备用摘要
            
        Returns:
            提取的文本内容
        """
        try:
            text_content = ""
            
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                num_pages = min(len(reader.pages), Config.MAX_PDF_PAGES)
                
                logger.info(f"提取PDF内容，限制为{num_pages}页")
                
                # 提取前n页文本内容
                for i in range(num_pages):
                    try:
                        page = reader.pages[i]
                        page_text = page.extract_text()
                        if page_text:
                            text_content += page_text + "\n\n"
                    except Exception as e:
                        logger.warning(f"提取第{i+1}页内容失败: {e}")
            
            # 处理内容长度
            text_len = len(text_content)
            if text_len < 100:
                logger.warning("PDF内容提取失败或内容过少，可能是扫描版")
                return self._get_summary_from_paper_info(pdf_path, current_papers)
            elif text_len > Config.MAX_CONTENT_LENGTH:
                logger.info(f"截断PDF内容从{text_len}到{Config.MAX_CONTENT_LENGTH}字符")
                return text_content[:Config.MAX_CONTENT_LENGTH] + "...\n[内容已截断]"
            
            return text_content
            
        except Exception as e:
            logger.error(f"PDF内容提取失败: {e}")
            return self._get_summary_from_paper_info(pdf_path, current_papers)
    
    def _get_summary_from_paper_info(self, pdf_path: str, current_papers: List[Dict] = None) -> str:
        """
        当无法从PDF提取内容时，使用论文信息构建摘要
        
        Args:
            pdf_path: PDF文件路径
            current_papers: 当前论文列表
        """
        # 从文件名获取论文ID
        paper_id = Path(pdf_path).stem
        
        # 查找对应论文信息
        if current_papers:
            for paper in current_papers:
                if paper['id'] == paper_id:
                    return f"""标题: {paper['title']}
作者: {', '.join(paper['authors'])}
摘要: {paper['summary']}"""
        
        return "无法获取论文信息"
    
    def download_paper_content(self, paper: Dict, pdf_path: str) -> Optional[str]:
        """
        获取论文内容用于AI总结
        
        Args:
            paper: 论文信息字典
            pdf_path: PDF文件路径
            
        Returns:
            论文内容
        """
        try:
            # 提取PDF内容，传递论文信息作为备用
            pdf_text = self.extract_text_from_pdf(pdf_path, [paper])
            
            # 组合论文元数据和PDF内容
            content = f"""# {paper['title']}

## 作者
{', '.join(paper['authors'])}

## 发布日期
{paper['published'][:10] if paper['published'] != "日期不可用" else paper['published']}

## ArXiv ID
{paper['id']}

## 摘要
{paper['summary']}

## PDF内容
{pdf_text}
"""
            return content
        except Exception as e:
            logger.error(f"提取论文 {paper['id']} 内容时出错: {e}")
            return None
    
    def summarize_paper_with_llm(self, content: str, paper_title: str) -> str:
        """使用大模型对论文进行详细总结"""
        if not self.client:
            return "无法生成AI总结：未配置API密钥"
        
        # 限制输入内容大小
        if len(content) > Config.MAX_CONTENT_LENGTH:
            logger.info(f"内容过长，截断至{Config.MAX_CONTENT_LENGTH}字符")
            content = content[:Config.MAX_CONTENT_LENGTH] + "\n...[内容已截断]"
        
        prompt = f"""请对以下论文进行详细总结分析，包括：
1. 研究背景和问题
2. 主要贡献和创新点
3. 方法论
4. 实验结果和结论

请用中文总结，格式清晰，各部分用标题分隔。
如果论文内容不完整，请根据现有内容进行总结。
你需要总结得更可能详细，当论文内容存在图片或者表格时，
应尽量保持其完整的输出，并且附上解释。

论文内容：
{content}
"""
        
        logger.info(f"正在生成论文总结: {paper_title}")
        
        # 使用配置中的重试次数
        for attempt in range(Config.MAX_DOWNLOAD_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "你是专业学术论文分析师，擅长总结科学论文。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1500,
                    temperature=0.2
                )
                
                summary = response.choices[0].message.content
                logger.info(f"总结生成成功，长度: {len(summary)}字符")
                return summary
                
            except Exception as e:
                if attempt < Config.MAX_DOWNLOAD_RETRIES - 1:
                    logger.warning(f"总结生成失败，尝试重试: {e}")
                    time.sleep(Config.RETRY_DELAY)
                else:
                    logger.error(f"总结生成失败: {e}")
                    return f"无法生成总结: {str(e)}"
        
        return "总结生成失败，请重试"
    
    def save_summary_as_html(self, summary: str, paper: Dict) -> str:
        """将论文总结保存为HTML格式"""
        # 将Markdown格式的总结转换为HTML
        html_content = markdown.markdown(summary)
        
        # 简化的HTML模板
        full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>论文总结 - {html.escape(paper['title'][:50])}</title>
    <style>
        body {{ font-family: 'Arial', sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f5f5f5; }}
        .container {{ background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 25px; }}
        .paper-info {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .summary-content {{ text-align: justify; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>论文总结</h1>
        <div class="paper-info">
            <h2>论文信息</h2>
            <p><strong>标题：</strong>{html.escape(paper['title'])}</p>
            <p><strong>作者：</strong>{html.escape(', '.join(paper['authors']))}</p>
            <p><strong>发布日期：</strong>{paper['published'][:10]}</p>
            <p><strong>ArXiv ID：</strong>{paper['id']}</p>
            <p><strong>PDF链接：</strong><a href="{paper['pdf_link']}" target="_blank">{paper['pdf_link']}</a></p>
        </div>
        <div class="summary-content">
            <h2>详细总结</h2>
            {html_content}
        </div>
    </div>
</body>
</html>"""
        
        filename = f"{paper['id']}_summary.html"
        filepath = self.data_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_html)
            return str(filepath)
        except Exception as e:
            logger.error(f"保存HTML文件失败: {e}")
            return ""
    
    def generate_summary(self, paper: Dict, pdf_path: str) -> Optional[str]:
        """
        生成论文总结的完整流程
        
        Args:
            paper: 论文信息字典
            pdf_path: PDF文件路径
            
        Returns:
            HTML文件路径或None
        """
        try:
            # 获取内容并总结
            content = self.download_paper_content(paper, pdf_path)
            if not content:
                logger.error("无法获取论文内容")
                return None
            
            # AI总结
            paper_title = paper['title'][:50] + ('...' if len(paper['title']) > 50 else '')
            summary = self.summarize_paper_with_llm(content, paper_title)
            if summary:
                html_path = self.save_summary_as_html(summary, paper)
                if html_path:
                    logger.info(f"总结已保存: {html_path}")
                    return html_path
            
            return None
            
        except Exception as e:
            logger.error(f"生成总结过程出错: {e}")
            return None
