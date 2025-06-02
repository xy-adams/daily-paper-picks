import os
from pathlib import Path
from arxiv_crawler import ArxivPaperCrawler
from arxiv_process import ArxivPDFProcessor
from arxiv_summary import ArxivSummaryGenerator
from arxiv_research import ArxivResearcher
from auto_email import send_email
from config import Config
from utils import setup_logger, validate_email
import schedule
import time
from datetime import datetime

# 配置日志
logger = setup_logger(__name__)

def read_html_content(file_path: str) -> str:
    """读取HTML文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取HTML文件失败: {e}")
        return None

def process_and_send(topic: str, target_email: str, max_papers: int = 5) -> bool:
    """
    处理论文并发送邮件
    
    Args:
        topic: 搜索主题
        target_email: 目标邮箱地址
        max_papers: 最大论文数量
        
    Returns:
        bool: 处理是否成功
    """
    try:
        # 获取data目录路径
        data_dir = Path(Config.DATA_DIR)
        if not data_dir.exists():
            data_dir.mkdir(parents=True)
        
        # 1. 搜索论文
        logger.info(f"开始搜索主题: {topic}")
        summary_generator = ArxivSummaryGenerator()
        researcher = ArxivResearcher(ai_client=summary_generator)
        papers = researcher.search_papers(topic, max_papers)
        
        if not papers:
            logger.warning("未找到符合条件的论文")
            return False
        
        logger.info(f"找到 {len(papers)} 篇论文")
        
        # 显示论文统计信息
        stats = researcher.get_paper_statistics(papers)
        if stats:
            logger.info(f"论文统计: 总数={stats['total_papers']}")
            if stats.get('top_categories'):
                top_cats = [f"{cat}({count})" for cat, count in stats['top_categories'][:3]]
                logger.info(f"主要分类: {', '.join(top_cats)}")
        
        # 2. 批量下载PDF
        pdf_processor = ArxivPDFProcessor(data_dir=str(data_dir))
        
        logger.info("开始批量下载PDF...")
        download_results = pdf_processor.batch_download_pdfs(papers)
        
        # 3. 检查AI配置
        if not Config.has_ai_config():
            logger.warning("未配置API密钥，跳过AI总结生成")
            return False
        
        # 4. 处理成功下载的论文
        successful_downloads = []
        for paper_id, result in download_results.items():
            paper = next((p for p in papers if p['id'] == paper_id), None)
            if paper and not result.startswith("下载PDF失败") and not result.startswith("处理论文"):
                successful_downloads.append((paper, result))
        
        logger.info(f"成功下载 {len(successful_downloads)} 篇论文，开始生成总结...")
        
        if not successful_downloads:
            logger.error("没有成功下载任何论文")
            return False
        
        # 5. 生成总结并发送邮件
        papers_list = [item[0] for item in successful_downloads]
        pdf_paths_list = [item[1] for item in successful_downloads]
        
        # 使用ArxivSummaryGenerator的新方法生成合并总结
        combined_content = summary_generator.generate_combined_summary(papers_list, pdf_paths_list, topic)
        
        if not combined_content:
            logger.error("总结生成失败")
            return False
        
        # 6. 发送邮件
        if len(papers_list) == 1:
            subject = f"ArXiv论文总结 - {papers_list[0]['title'][:30]}..."
        else:
            subject = f"ArXiv论文总结合集 - {topic} ({len(papers_list)}篇)"
        
        logger.info(f"正在发送邮件到: {target_email}")
        if send_email(target_email, combined_content, subject):
            if len(papers_list) == 1:
                logger.info(f"✓ 邮件发送成功")
            else:
                logger.info(f"✓ 合并邮件发送成功，包含 {len(papers_list)} 篇论文")
            return True
        else:
            logger.error(f"✗ 邮件发送失败")
            return False
        
    except Exception as e:
        logger.error(f"处理过程出错: {e}")
        return False

def get_user_config() -> dict:
    """获取用户配置"""
    print("=== ArXiv论文自动总结与邮件发送系统 ===")
    print("本程序将搜索ArXiv论文，下载PDF，生成AI总结，并发送到指定邮箱")
    print()
    
    # 检查配置
    config_status = Config.validate_config()
    if not config_status['ai_configured']:
        logger.error("AI配置未设置，请配置MODEL_API_KEY环境变量")
        return None
    
    if not config_status['email_configured']:
        logger.error("邮件配置未设置，请配置RESEND_API_KEY环境变量")
        return None
    
    # 获取用户输入
    topic = input("请输入要搜索的论文主题: ").strip()
    if not topic:
        logger.error("搜索主题不能为空")
        return None
    
    target_email = input("请输入目标邮箱地址: ").strip()
    if not validate_email(target_email):
        logger.error("请输入有效的邮箱地址")
        return None
    
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
    
    return {
        'topic': topic,
        'target_email': target_email,
        'max_papers': max_papers
    }

def scheduled_task():
    """定时任务函数"""
    try:
        print(f"\n=== 定时任务开始执行 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ===")
        
        # 从环境变量获取配置
        topic = os.getenv('SCHEDULED_TOPIC')
        target_email = os.getenv('SCHEDULED_EMAIL')
        max_papers = int(os.getenv('SCHEDULED_MAX_PAPERS'))
        
        if not target_email:
            logger.error("定时任务需要设置SCHEDULED_EMAIL环境变量")
            return
        
        if not validate_email(target_email):
            logger.error(f"无效的邮箱地址: {target_email}")
            return
        
        print(f"搜索主题: '{topic}'")
        print(f"目标邮箱: {target_email}")
        print(f"最大论文数: {max_papers}")
        print("开始执行任务...\n")
        
        # 执行处理和发送
        success = process_and_send(topic, target_email, max_papers)
        
        if success:
            print(f"\n=== 定时任务执行成功 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ===")
        else:
            print(f"\n=== 定时任务执行失败 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ===")
        
    except Exception as e:
        logger.error(f"定时任务执行出错: {e}")

def run_scheduler():
    """运行定时任务调度器"""
    print("=== ArXiv论文自动总结定时任务系统 ===")
    print(f"程序将每天 {Config.SCHEDULED_TIME} 自动执行论文搜索和总结任务")
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("按 Ctrl+C 停止程序")
    print()
    
    # 检查环境变量配置
    if not os.getenv('SCHEDULED_EMAIL'):
        print("注意：定时任务需要设置以下环境变量：")
        print("- SCHEDULED_EMAIL: 目标邮箱地址（必需）")
        print("- SCHEDULED_TOPIC: 搜索主题（必需）")
        print("- SCHEDULED_MAX_PAPERS: 最大论文数（必需）")
        print(f"- SCHEDULED_TIME: 执行时间（可选，默认为{Config.SCHEDULED_TIME}）")
        print()
    
    # 设置定时任务：使用配置中的时间
    schedule.every().day.at(Config.SCHEDULED_TIME).do(scheduled_task)
    
    # 可选：添加立即执行一次的选项（用于测试）
    user_input = input("是否立即执行一次任务进行测试？(y/n): ").strip().lower()
    if user_input == 'y':
        print("立即执行测试任务...")
        scheduled_task()
    
    print(f"\n定时任务已设置，将在每天 {Config.SCHEDULED_TIME} 执行")
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
        config = get_user_config()
        if not config:
            return
        
        print(f"\n开始处理主题: '{config['topic']}'，最大论文数: {config['max_papers']}")
        print("这可能需要一些时间，请耐心等待...\n")
        
        # 处理并发送
        success = process_and_send(config['topic'], config['target_email'], config['max_papers'])
        
        if success:
            logger.info("程序运行完成！")
        else:
            logger.error("程序运行失败！")
        
    except KeyboardInterrupt:
        logger.info("\n用户中断，程序退出")
    except Exception as e:
        logger.error(f"程序执行出错: {e}")

def main():
    """主函数"""
    try:
        print("请选择运行模式:")
        print("1. 立即执行一次")
        print("2. 定时任务模式 (每天定时执行)")
        
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
