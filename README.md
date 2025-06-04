# ArXiv论文自动总结与邮件发送系统

一个全自动的学术论文处理系统，能够搜索ArXiv上的最新论文，下载PDF文件，使用AI生成中文总结，并通过邮件发送给用户。

## 🚀 功能特性

- **智能搜索**: 支持主题搜索、分类搜索、作者搜索和日期范围搜索
- **自动下载**: 批量下载PDF文件，支持断点续传和文件验证
- **AI总结**: 使用GPT、deepseek等模型生成高质量的中文论文总结
- **邮件发送**: 自动将总结以精美的HTML格式发送到指定邮箱
- **定时任务**: 支持可配置的定时执行任务
- **错误处理**: 完善的错误处理和重试机制
- **日志记录**: 详细的日志记录，便于问题排查

## 📁 项目结构

```
auto_paper/
├── main.py              # 主程序入口
├── config.py            # 配置管理模块
├── utils.py             # 通用工具模块
├── arxiv_research.py    # 论文搜索模块
├── arxiv_process.py     # PDF处理模块
├── arxiv_summary.py     # AI总结生成模块
├── auto_email.py        # 邮件发送模块
├── arxiv_crawler.py     # 论文爬虫模块
├── requirements.txt     # 依赖包列表
├── env_example.txt      # 环境变量配置示例
├── README.md           # 项目说明文档
└── data/               # 数据存储目录
    ├── *.pdf           # 下载的PDF文件
    └── *.html          # 生成的总结文件
```

## ⚙️ 环境配置

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
复制环境变量模板文件：
```bash
cp env_example.txt .env
```

在 `.env` 文件中配置以下参数：

#### AI 模型配置（必需）
```env
# OpenAI API 密钥
MODEL_API_KEY=your_openai_api_key_here

# API 基础URL（可选）
MODEL_BASE_URL=https://api.openai.com/v1

# 模型名称（可选，默认为gpt-3.5-turbo）
MODEL_NAME=gpt-3.5-turbo
```

#### 邮件服务配置（必需）
```env
# Resend API 密钥
RESEND_API_KEY=your_resend_api_key_here

# 发件人邮箱地址（推荐使用默认地址）
EMAIL_FROM=ArXiv论文助手 <onboarding@resend.dev>
```
resend的apikey在网站https://resend.com/emails上申请

#### 定时任务配置（定时模式需要）
```env
# 目标邮箱地址
SCHEDULED_EMAIL=your_target_email@example.com

# 搜索主题
SCHEDULED_TOPIC=Large Language Model

# 最大论文数
SCHEDULED_MAX_PAPERS=1

# 执行时间（格式HH:MM，默认07:00）
SCHEDULED_TIME=07:00
```

## 🚀 使用方法

### 运行主程序
```bash
python main.py
```

程序提供两种运行模式：

1. **立即执行模式**：交互式配置并立即执行
2. **定时任务模式**：按配置的时间自动执行


## 📚 核心模块说明

### 1. config.py - 配置管理
集中管理所有配置项，支持环境变量和默认值：

```python
# 主要配置项
MODEL_API_KEY        # AI API密钥
RESEND_API_KEY       # 邮件服务API密钥
EMAIL_FROM           # 发件人地址
SCHEDULED_TIME       # 定时任务执行时间
DATA_DIR             # 数据存储目录
MAX_PDF_PAGES        # PDF最大处理页数
MAX_CONTENT_LENGTH   # 最大内容长度
```

### 2. arxiv_research.py - 论文搜索
智能论文搜索和相关性评分：

```python
researcher = ArxivResearcher()

# 主题搜索
papers = researcher.search_papers("machine learning", max_results=10)

# 相关性搜索
papers = researcher.search_papers_with_relevance(
    "transformer", max_results=10, strategy="comprehensive"
)

# 分类搜索
papers = researcher.search_papers_by_category("cs.LG", max_results=5)
```

### 3. arxiv_process.py - PDF处理
高效的PDF下载和验证：

```python
processor = ArxivPDFProcessor()

# 批量下载
results = processor.batch_download_pdfs(papers)

# 文件验证
is_valid = processor.validate_pdf_file(pdf_path)
```

### 4. arxiv_summary.py - AI总结
智能论文总结生成：

```python
generator = ArxivSummaryGenerator()

# 生成总结
html_path = generator.generate_summary(paper_info, pdf_path)
```

### 5. auto_email.py - 邮件发送
精美的HTML邮件发送：

```python
# 发送邮件
success = send_email(
    to_email="user@example.com",
    content=html_content,
    subject="论文总结"
)
```

## 🔧 高级功能

### 自定义搜索策略
```python
# 精确搜索
papers = researcher.search_papers_with_relevance(
    topic="transformer", 
    strategy="precise",
    min_relevance=0.5
)

# 综合搜索
papers = researcher.search_papers_with_relevance(
    topic="deep learning", 
    strategy="comprehensive"
)
```

### 日期范围搜索
```python
papers = researcher.search_papers_by_date_range(
    topic="computer vision",
    start_date="2023-01-01",
    end_date="2023-12-31"
)
```

### 作者搜索
```python
papers = researcher.search_papers_by_author("Yoshua Bengio")
```

## 📊 论文统计分析
```python
# 获取统计信息
stats = researcher.get_paper_statistics(papers)
print(f"找到 {stats['total_papers']} 篇论文")
print(f"平均相关性: {stats['average_relevance']}")

# 获取详细洞察
insights = researcher.get_paper_insights(papers, topic)
```

## ⚠️ 注意事项

### 邮件配置
- **推荐使用默认发件地址**：`onboarding@resend.dev`
- **自定义域名**：需要在 [Resend](https://resend.com/domains) 验证域名
- **API限制**：注意Resend的发送频率限制

### AI模型配置
- 支持OpenAI兼容的API服务
- 建议使用 `gpt-3.5-turbo` 或更高版本
- 内容会自动截断到配置的最大长度

### 文件存储
- PDF文件和HTML总结保存在 `./data` 目录
- 支持断点续传，重复运行时会跳过已下载文件
- 定期清理无效文件以节省空间

## 🐛 故障排除

### 邮件发送失败
```
错误：domain is not verified
解决：使用默认地址 onboarding@resend.dev 或验证自定义域名
```

### PDF下载失败
- 检查网络连接
- 某些论文可能暂时不可用
- 程序会自动重试并记录错误

### AI总结生成失败
- 检查API密钥是否正确
- 确认API配额是否充足
- 检查网络连接

## 🔄 版本更新

### v2.0.0 (当前版本)
**重大改进**:
- 完全重构代码架构，模块化设计
- 新增配置管理系统
- 优化PDF下载性能和稳定性
- 改进AI总结质量和格式
- 现代化的HTML邮件模板
- 完善的错误处理和重试机制
- 添加进度跟踪和用户反馈

**新功能**:
- 支持多种搜索方式
- 批量处理优化
- 存储管理功能
- 配置验证系统

### v1.0.0 - 初始版本
- 基本的论文搜索和下载功能
- 简单的AI总结生成
- 基础的邮件发送功能

## 📄 许可证

本项目采用 MIT 许可证，详见 `LICENSE` 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进项目！

## 📞 支持

如有问题，请在 GitHub 上创建 Issue。