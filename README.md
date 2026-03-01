# YouTube 视频摘要自动化工具

一个自动化的 YouTube 视频摘要工具，从配置文件读取视频列表，自动获取字幕、生成摘要，输出 Markdown 博客文件。

## 功能特性

- ✅ **完全自动化**：一行命令完成字幕获取 → AI 摘要 → 生成博客
- ✅ **AI 智能摘要**：支持 Claude API（推荐）或 OpenAI API 自动生成中文摘要
- ✅ **两种模式**：Brief（简洁摘要）和 Detailed（详细学习笔记）
- ✅ **增量更新**：自动跳过已处理的视频，只处理新视频
- ✅ **多语言支持**：自动检测视频语言，支持任意语言字幕

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key（用于 AI 摘要）

```bash
# 方式 1：使用 Claude API（推荐）
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# 方式 2：使用 OpenAI API
export OPENAI_API_KEY="your-openai-api-key"
```

### 3. 创建配置文件

创建 `videos.yaml`：

```yaml
videos:
  - url: https://www.youtube.com/watch?v=xxxxx
    mode: brief        # 简洁摘要（3-5个要点）

  - url: https://www.youtube.com/watch?v=yyyyy
    mode: detailed     # 详细学习笔记

settings:
  default_mode: brief
  output_file: ./output/my_blog.md
```

### 4. 运行自动化

```bash
# 处理新视频（跳过已处理的）
python auto_blog.py

# 重新处理所有视频
python auto_blog.py --rebuild

# 预览模式
python auto_blog.py --dry-run
```

## 命令行参数

```
python auto_blog.py --help

参数:
  --config, -c    配置文件路径（默认: videos.yaml）
  --output, -o    输出博客文件路径
  --rebuild       强制重新处理所有视频
  --dry-run       预览模式，不实际处理
  --no-ai         禁用 AI 摘要，仅获取字幕
```

## 模式对比

| 模式 | 输出内容 | 适用场景 |
|------|----------|----------|
| `brief` | 3-5 个核心要点 | 快速了解视频内容 |
| `detailed` | 分章节学习笔记 | 深入学习和复习 |

## 项目结构

```
.
├── auto_blog.py              # 自动化主入口
├── blog_main.py              # 批量博客模式（交互式）
├── videos.yaml               # 配置文件
├── src/
│   ├── blog_generator.py     # 博客生成器
│   ├── summary_generator.py  # AI 摘要生成器
│   ├── transcript_fetcher.py # 字幕获取
│   └── config_parser.py      # 配置解析
├── output/
│   ├── my_blog.md            # 生成的博客
│   └── my_blog_meta.json     # 元数据（增量更新）
└── requirements.txt
```

## 费用说明

| 功能 | 费用 |
|------|------|
| 字幕获取 | 免费 |
| Claude API 摘要 | ~$0.01-0.05/视频 |
| OpenAI API 摘要 | ~$0.02-0.10/视频 |
| 无 API Key | 生成占位符，手动填写 |

## 更新日志

### 2026-03-01
- ✅ **完全自动化**：新增 `auto_blog.py`，一行命令完成全部流程
- ✅ **AI 自动摘要**：支持 Claude/OpenAI API 自动生成中文摘要
- ✅ **增量更新优化**：自动去重，避免重复处理
- ✅ **修复目录重复**：元数据加载时自动去重
