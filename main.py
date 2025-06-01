import os
from pathlib import Path
from arxiv_crawler import ArxivPaperCrawler
from arxiv_process import ArxivPDFProcessor
from arxiv_summary import ArxivSummaryGenerator
from arxiv_research import ArxivResearcher
from auto_email import send_email
import logging
import schedule
import time
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_html_content(file_path: str) -> str:
    """读取HTML文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取HTML文件失败: {e}")
        return None

def process_and_send(topic: str, target_email: str, max_papers: int = 5):
    """
    处理论文并发送邮件
    
    Args:
        topic: 搜索主题
        target_email: 目标邮箱地址
        max_papers: 最大论文数量
    """
    try:
        # 获取data目录路径
        data_dir = Path("./data")
        if not data_dir.exists():
            data_dir.mkdir(parents=True)
        
        # 设置代理
        proxies = None
        http_proxy = os.getenv('HTTP_PROXY')
        https_proxy = os.getenv('HTTPS_PROXY')
        
        if http_proxy or https_proxy:
            proxies = {}
            if http_proxy:
                proxies['http'] = http_proxy
            if https_proxy:
                proxies['https'] = https_proxy
            logger.info(f"使用代理设置: {proxies}")
        
        # 1. 搜索论文 - 使用新的研究器
        logger.info(f"开始搜索主题: {topic}")
        summary_generator = ArxivSummaryGenerator()
        researcher = ArxivResearcher(proxies=proxies, ai_client=summary_generator)
        papers = researcher.search_papers(topic, max_papers)
        
        if not papers:
            logger.warning("未找到符合条件的论文")
            return
        
        logger.info(f"找到 {len(papers)} 篇论文")
        
        # 显示论文统计信息
        stats = researcher.get_paper_statistics(papers)
        if stats:
            logger.info(f"论文统计: 总数={stats['total_papers']}")
            if stats.get('top_categories'):
                top_cats = [f"{cat}({count})" for cat, count in stats['top_categories'][:3]]
                logger.info(f"主要分类: {', '.join(top_cats)}")
        
        # 2. 批量下载PDF
        pdf_processor = ArxivPDFProcessor(
            data_dir=str(data_dir),
            proxies=proxies
        )
        
        logger.info("开始批量下载PDF...")
        download_results = pdf_processor.batch_download_pdfs(papers)
        
        # 3. 生成总结（使用已创建的生成器）
        
        if not summary_generator.client:
            logger.warning("未配置API密钥，跳过AI总结生成")
            return
        
        successful_downloads = []
        for paper_id, result in download_results.items():
            # 找到对应的论文信息
            paper = next((p for p in papers if p['id'] == paper_id), None)
            if paper and not result.startswith("下载PDF失败") and not result.startswith("处理论文"):
                successful_downloads.append((paper, result))
        
        logger.info(f"成功下载 {len(successful_downloads)} 篇论文，开始生成总结...")
        
        # 4. 为每篇成功下载的论文生成总结并发送邮件
        sent_count = 0
        for paper, pdf_path in successful_downloads:
            try:
                logger.info(f"处理论文: {paper['title'][:50]}...")
                
                # 生成总结
                html_path = summary_generator.generate_summary(paper, pdf_path)
                if not html_path:
                    logger.error(f"总结生成失败: {paper['id']}")
                    continue
                
                # 读取HTML内容
                content = read_html_content(html_path)
                if not content:
                    logger.error(f"读取总结文件失败: {html_path}")
                    continue
                
                # 发送邮件
                subject = f"ArXiv论文总结 - {paper['title'][:30]}..."
                logger.info(f"正在发送邮件到: {target_email}")
                result = send_email(target_email, content, subject)
                
                if result:
                    logger.info(f"✓ 邮件发送成功: {paper['id']}")
                    sent_count += 1
                else:
                    logger.error(f"✗ 邮件发送失败: {paper['id']}")
                
            except Exception as e:
                logger.error(f"处理论文 {paper['id']} 时出错: {e}")
                continue
        
        logger.info(f"处理完成！成功发送 {sent_count}/{len(successful_downloads)} 篇论文总结")
        
    except Exception as e:
        logger.error(f"处理过程出错: {e}")

def scheduled_task():
    """定时任务函数"""
    try:
        print(f"\n=== 定时任务开始执行 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ===")
        
        # 固定的配置参数
        topic = "Large Language Model"
        target_email = "xy_wbfq@163.com"
        max_papers = 1
        
        print(f"搜索主题: '{topic}'")
        print(f"目标邮箱: {target_email}")
        print(f"最大论文数: {max_papers}")
        print("开始执行任务...\n")
        
        # 执行处理和发送
        process_and_send(topic, target_email, max_papers)
        
        print(f"\n=== 定时任务执行完成 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ===")
        
    except Exception as e:
        logger.error(f"定时任务执行出错: {e}")

def run_scheduler():
    """运行定时任务调度器"""
    print("=== ArXiv论文自动总结定时任务系统 ===")
    print("程序将每天早上7:00自动执行论文搜索和总结任务")
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("按 Ctrl+C 停止程序")
    print()
    
    # 设置定时任务：每天早上7点执行
    schedule.every().day.at("16:55").do(scheduled_task)
    
    # 可选：添加立即执行一次的选项（用于测试）
    user_input = input("是否立即执行一次任务进行测试？(y/n): ").strip().lower()
    if user_input == 'y':
        print("立即执行测试任务...")
        scheduled_task()
    
    print(f"\n定时任务已设置，将在每天 07:00 执行")
    print("等待定时任务触发中...")
    
    # 持续运行调度器
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    except KeyboardInterrupt:
        print("\n用户中断，定时任务停止")
        logger.info("定时任务调度器已停止")

def run_once():
    """立即执行一次任务"""
    try:
        print("=== ArXiv论文自动总结与邮件发送系统 ===")
        print("本程序将搜索ArXiv论文，下载PDF，生成AI总结，并发送到指定邮箱")
        print()
        
        # 获取用户输入
        topic = input("请输入要搜索的论文主题: ").strip()
        if not topic:
            logger.error("搜索主题不能为空")
            return
        target_email = input("请输入目标邮箱地址: ").strip()
        if not target_email or '@' not in target_email:
            logger.error("请输入有效的邮箱地址")
            return
        
        # 询问论文数量
        try:
            max_papers_input = input("请输入要处理的最大论文数量 (默认5篇): ").strip()
            max_papers = int(max_papers_input) if max_papers_input else 5
            if max_papers <= 0 or max_papers > 20:
                logger.warning("论文数量应在1-20之间，使用默认值5")
                max_papers = 5
        except ValueError:
            logger.warning("输入的论文数量无效，使用默认值5")
            max_papers = 5
        
        print(f"\n开始处理主题: '{topic}'，最大论文数: {max_papers}")
        print("这可能需要一些时间，请耐心等待...\n")
        
        # 处理并发送
        process_and_send(topic, target_email, max_papers)
        
        logger.info("程序运行完成！")
        
    except KeyboardInterrupt:
        logger.info("\n用户中断，程序退出")
    except Exception as e:
        logger.error(f"程序执行出错: {e}")

def main():
    """主函数"""
    try:
        print("请选择运行模式:")
        print("1. 立即执行一次")
        print("2. 定时任务模式 (每天早上7:00执行)")
        
        choice = input("请输入选择 (1 或 2): ").strip()
        
        if choice == "1":
            run_once()
        elif choice == "2":
            run_scheduler()
        else:
            print("无效选择，默认使用立即执行模式")
            run_once()
            
    except KeyboardInterrupt:
        logger.info("\n用户中断，程序退出")
    except Exception as e:
        logger.error(f"程序执行出错: {e}")

if __name__ == "__main__":
    main()
