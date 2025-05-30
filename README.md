# ArXiv论文自动总结与邮件发送系统

一个全自动的学术论文处理系统，能够搜索ArXiv上的最新论文，下载PDF文件，使用AI生成中文总结，并通过邮件发送给用户。

## 🚀 功能特性

- **智能搜索**: 支持主题搜索、分类搜索、作者搜索和日期范围搜索
- **自动下载**: 批量下载PDF文件，支持断点续传和文件验证
- **AI总结**: 使用OpenAI GPT模型生成高质量的中文论文总结
- **邮件发送**: 自动将总结以精美的HTML格式发送到指定邮箱
- **代理支持**: 支持HTTP/HTTPS代理，适应各种网络环境
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
├── arxiv_crawler.py     # 论文爬虫模块(兼容旧版)
├── test_modules.py      # 测试模块
├── requirements.txt     # 依赖包列表
├── README.md           # 项目说明文档
└── data/               # 数据存储目录
    ├── *.pdf           # 下载的PDF文件
    └── *.html          # 生成的总结文件
```

## 📚 模块功能详解

### 1. config.py - 配置管理模块
**功能**: 集中管理所有配置项，提高代码的可维护性

**主要特性**:
- 统一管理API密钥、代理设置、文件路径等配置
- 支持环境变量和默认值
- 提供配置验证功能

**关键配置项**:
```python
# AI模型配置
MODEL_API_KEY     # OpenAI API密钥
MODEL_BASE_URL    # API基础URL
MODEL_NAME        # 使用的模型名称

# 邮件配置
RESEND_API_KEY    # Resend邮件服务API密钥
EMAIL_FROM        # 发件人地址

# 网络配置
HTTP_PROXY        # HTTP代理
HTTPS_PROXY       # HTTPS代理
```

### 2. utils.py - 通用工具模块
**功能**: 提供项目中常用的辅助函数

**主要功能**:
- 日志记录器设置
- 重试装饰器
- 文件操作工具
- 文本处理函数
- 进度跟踪器

**核心工具**:
```python
setup_logger()      # 设置标准化日志
retry()             # 重试装饰器
ensure_directory()  # 确保目录存在
validate_email()    # 邮箱地址验证
ProgressTracker     # 进度跟踪类
```

### 3. arxiv_research.py - 论文搜索模块
**功能**: 负责从ArXiv搜索和获取论文信息

**主要功能**:
- 智能查询生成（可使用AI优化搜索词）
- 多种搜索方式：主题、分类、作者、日期范围
- 论文信息解析和标准化
- 搜索结果统计分析

**使用示例**:
```python
researcher = ArxivResearcher()

# 主题搜索
papers = researcher.search_papers("machine learning", max_results=10)

# 分类搜索
papers = researcher.search_papers_by_category("cs.LG", max_results=5)

# 作者搜索
papers = researcher.search_papers_by_author("Yoshua Bengio", max_results=5)

# 日期范围搜索
papers = researcher.search_papers_by_date_range(
    "deep learning", "2023-01-01", "2023-12-31", max_results=10
)
```

### 4. arxiv_process.py - PDF处理模块
**功能**: 负责下载和验证PDF文件

**主要功能**:
- 批量PDF下载，支持断点续传
- 文件完整性验证
- 下载进度显示
- 存储管理和清理

**核心特性**:
- 流式下载，节省内存
- 多重验证：文件大小、PDF格式、内容完整性
- 自动重试机制
- 代理支持

**使用示例**:
```python
processor = ArxivPDFProcessor()

# 单个文件下载
success, path = processor.download_paper_pdf(paper_info)

# 批量下载
results = processor.batch_download_pdfs(papers_list)

# 获取存储信息
storage_info = processor.get_storage_info()
```

### 5. arxiv_summary.py - AI总结生成模块
**功能**: 使用AI生成论文的中文总结

**主要功能**:
- PDF文本提取和预处理
- AI驱动的智能总结生成
- 多格式输出：Markdown、HTML
- 精美的HTML模板

**总结内容结构**:
1. **研究背景**: 简述研究领域和要解决的问题
2. **主要贡献**: 列出论文的核心创新点和贡献
3. **方法论**: 概述使用的研究方法和技术路线
4. **实验结果**: 总结关键实验结果和性能指标
5. **结论与影响**: 论文的主要结论和潜在影响

**使用示例**:
```python
generator = ArxivSummaryGenerator()

# 生成单篇总结
html_path = generator.generate_summary(paper_info, pdf_path)

# 批量生成总结
results = generator.batch_generate_summaries(papers_and_pdfs)
```

### 6. auto_email.py - 邮件发送模块
**功能**: 发送精美的HTML格式邮件

**主要功能**:
- 响应式HTML邮件模板
- 批量邮件发送
- 邮箱地址验证
- 发送状态跟踪

**邮件特性**:
- 现代化的设计风格
- 移动端适配
- 包含论文完整信息
- 自动生成时间戳

**使用示例**:
```python
sender = EmailSender()

# 发送单篇论文总结
success = sender.send_paper_summary(
    to_email="user@example.com",
    paper_title="论文标题",
    content=html_content
)
```

### 7. main.py - 主程序模块
**功能**: 整合所有模块，提供完整的处理流程

**核心类: ArxivPaperProcessor**
- 统一管理所有子模块
- 提供完整的工作流程
- 错误处理和状态报告
- 进度跟踪和用户反馈

**完整工作流程**:
1. 用户输入验证
2. 论文搜索和统计
3. PDF批量下载
4. AI总结生成
5. 邮件发送
6. 结果汇总报告

## 🛠️ 安装和配置

### 1. 环境要求
- Python 3.8+
- 稳定的网络连接
- OpenAI API 访问权限（用于AI总结）
- Resend邮件服务账户（用于邮件发送）

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 环境变量配置
创建 `.env` 文件或设置环境变量：

```bash
# AI模型配置
MODEL_API_KEY=your_openai_api_key
MODEL_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-3.5-turbo

# 邮件服务配置
RESEND_API_KEY=your_resend_api_key

# 代理配置（可选）
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=https://proxy.example.com:8080
```

## 🚀 使用方法

### 基本使用
```bash
python main.py
```

然后按照提示输入：
1. 搜索主题（如："machine learning"、"自然语言处理"等）
2. 目标邮箱地址
3. 最大论文数量（1-20篇）

### 高级使用
可以直接调用各个模块进行自定义操作：

```python
from main import ArxivPaperProcessor

# 创建处理器
processor = ArxivPaperProcessor()

# 执行完整工作流
results = processor.process_complete_workflow(
    topic="deep learning",
    target_email="user@example.com",
    max_papers=10
)

# 只下载论文（不生成总结）
papers_and_pdfs = processor.search_and_download_papers("AI", 5)

# 只生成总结（不发送邮件）
summaries = processor.generate_summaries(papers_and_pdfs)
```

## 📊 性能和限制

### 性能指标
- **搜索速度**: 通常2-5秒可完成10篇论文的搜索
- **下载速度**: 取决于网络状况，平均每篇论文1-3分钟
- **总结生成**: 每篇论文约30秒-2分钟（取决于API响应速度）
- **内存使用**: 约50-100MB（流式处理，不会占用大量内存）

### 使用限制
- **论文数量**: 单次最多处理20篇论文
- **PDF大小**: 建议单个PDF不超过50MB
- **API限制**: 受OpenAI API速率限制影响
- **网络要求**: 需要访问ArXiv和OpenAI API

## 🔧 故障排除

### 常见问题

1. **搜索不到论文**
   - 检查网络连接
   - 尝试更换搜索关键词
   - 检查代理设置

2. **PDF下载失败**
   - 检查网络稳定性
   - 验证代理配置
   - 查看日志获取详细错误信息

3. **总结生成失败**
   - 验证OpenAI API密钥
   - 检查API额度和限制
   - 确认网络可以访问OpenAI服务

4. **邮件发送失败**
   - 验证Resend API密钥
   - 检查邮箱地址格式
   - 查看邮件服务状态

### 日志查看
程序运行时会在控制台显示详细日志，包括：
- 搜索进度和结果
- 下载状态和错误
- AI处理过程
- 邮件发送结果

## 🔄 版本更新

### v2.0.0 (当前版本) - 2024年重构版
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

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交问题和功能请求！如果您想贡献代码，请：

1. Fork 本仓库
2. 创建您的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 📞 支持

如果您在使用过程中遇到问题，可以通过以下方式获取帮助：

1. 查看本文档的故障排除部分
2. 查看项目的 Issues 页面
3. 创建新的 Issue 描述您的问题

## ⭐ 致谢

感谢以下开源项目和服务：
- [ArXiv](https://arxiv.org/) - 提供免费的学术论文资源
- [OpenAI](https://openai.com/) - 提供强大的AI模型
- [Resend](https://resend.com/) - 提供可靠的邮件发送服务
- 所有相关的Python开源库的维护者