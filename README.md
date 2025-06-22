# ArXiv论文智能助手

一个自动获取、总结ArXiv论文并发送邮件的智能助手系统。系统支持定时任务、关键词搜索、AI总结生成等功能。

## 🚀 功能特性

- **智能搜索**: 支持关键词、分类、日期范围等多种搜索方式
- **内容爬取**: 使用Tavily API获取论文HTML内容
- **AI总结**: 使用大语言模型生成专业的中文论文总结
- **邮件发送**: 自动将总结结果发送到指定邮箱
- **定时任务**: 支持定时自动执行
- **多模块架构**: 清晰的代码结构，便于维护和扩展

## 📁 项目结构

```
daily-paper-picks/
├── core/                   # 核心功能模块
│   ├── arxiv_crawler.py   # 论文内容爬取
│   ├── arxiv_research.py  # 论文搜索和分析
│   ├── arxiv_summary.py   # AI总结生成
│   └── __init__.py
├── config/                 # 配置模块
│   ├── config.py          # 项目配置
│   └── __init__.py
├── utils/                  # 工具模块
│   ├── logger.py          # 日志工具
│   ├── email_sender.py    # 邮件发送
│   ├── file_utils.py      # 文件操作工具
│   ├── validators.py      # 数据验证
│   ├── common.py          # 通用工具
│   └── __init__.py
├── templates/              # 模板模块
│   ├── prompts.py         # AI提示词模板
│   └── __init__.py
├── scripts/                # 脚本文件
│   ├── start_scheduler.py # 定时任务启动脚本
│   └── start_scheduler.bat# Windows批处理脚本
├── data/                   # 数据存储目录
├── main.py                # 主程序入口
├── requirements.txt       # 依赖包列表
├── env_example.txt        # 环境变量示例
└── README.md              # 项目说明
```

## 🛠️ 安装配置

### 1. 环境要求

- Python 3.8+
- pip

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 环境配置

复制 `env_example.txt` 为 `.env` 文件，并填入相应的API密钥：

```env
# AI模型配置 (必需)
MODEL_API_KEY=your_openai_api_key
MODEL_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4

# 邮件服务配置 (必需)
RESEND_API_KEY=your_resend_api_key
EMAIL_FROM=noreply@yourdomain.com

# 爬虫配置 (必需)
TAVILY_API_KEY=your_tavily_api_key

# 定时任务配置 (可选)
SCHEDULED_TIME=07:00
SCHEDULED_TOPIC=machine learning
SCHEDULED_EMAIL=your@email.com
SCHEDULED_MAX_PAPERS=5
```

## 🚀 使用方法

### 交互式运行

```bash
python main.py
```

按提示输入：
- 搜索主题（如："machine learning"、"computer vision"等）
- 目标邮箱地址
- 处理的论文数量

### 定时任务运行

#### Linux/macOS:
```bash
python scripts/start_scheduler.py
```

#### Windows:
双击运行 `scripts/start_scheduler.bat`

### 单次执行

```bash
python main.py --once
```

## 📝 AI提示词自定义

系统将AI提示词独立到了 `templates/prompts.py` 文件中，你可以根据需要自定义：

```python
# 修改论文总结提示词
def get_paper_summary_prompt(paper_content: str) -> str:
    # 在这里自定义你的提示词模板
    pass
```

## 🔧 配置说明

### 核心配置项

- `MAX_CONTENT_LENGTH`: 单次处理的最大内容长度
- `AI_REQUEST_TIMEOUT`: AI请求超时时间
- `DATA_DIR`: 数据存储目录

### 邮件配置

使用 [Resend](https://resend.com/) 服务发送邮件：
1. 注册Resend账号获取API密钥
2. 配置发送邮箱域名
3. 设置环境变量

### AI模型配置

支持OpenAI兼容的API：
- OpenAI GPT系列
- Claude API
- 其他兼容接口

## 📊 功能模块说明

### ArxivResearcher (论文搜索)
- 支持关键词、分类、日期范围搜索
- 提供论文排序和过滤功能
- 统计分析功能

### ArxivContentCrawler (内容爬取)
- 使用Tavily API获取论文HTML内容
- 批量处理多篇论文
- 自动保存原始内容

### ArxivSummaryGenerator (AI总结)
- 使用大语言模型生成总结
- 支持自定义提示词模板
- 生成美观的HTML报告

## 🐛 常见问题

### 1. API密钥配置错误
确保 `.env` 文件中的API密钥正确且有效。

### 2. 网络连接问题
检查网络连接，某些API可能需要代理访问。

### 3. 内容长度限制
如果论文内容过长，系统会自动截取，可调整 `MAX_CONTENT_LENGTH` 参数。

### 4. 邮件发送失败
检查Resend API密钥和发送域名配置。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！

## 📧 联系方式

如有问题或建议，请通过GitHub Issues联系。

---

**本报告来源于晓勇的论文智能助手**