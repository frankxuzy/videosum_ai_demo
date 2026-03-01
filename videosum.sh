#!/bin/bash
# YouTube 视频博客生成器 - 命令行 wrapper
# 用法: ./videosum.sh [选项]

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 默认配置
CONFIG_FILE="my_videos.yaml"
MODE=""
REBUILD=false
DRY_RUN=false
VERBOSE=false

# 显示帮助信息
show_help() {
    cat << EOF
YouTube 视频博客生成器

用法:
  ./videosum.sh [选项]

选项:
  -c, --config <文件>    指定配置文件（默认: my_videos.yaml）
  -r, --rebuild          强制重新处理所有视频
  -d, --dry-run          试运行模式，不实际处理
  -v, --verbose          显示详细输出
  -h, --help             显示此帮助信息

示例:
  ./videosum.sh                           # 处理新视频（跳过已存在）
  ./videosum.sh -r                        # 重新处理所有视频
  ./videosum.sh -d                        # 试运行，检查配置
  ./videosum.sh -c new_videos.yaml        # 使用其他配置文件

配置文件示例 (my_videos.yaml):
  videos:
    - url: https://youtube.com/watch?v=xxx
      mode: detailed
    - url: https://youtube.com/watch?v=yyy
      mode: brief

  settings:
    default_mode: brief
    output_file: ./output/my_blog.md
EOF
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -r|--rebuild)
            REBUILD=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *.yaml|*.yml|*.json)
            CONFIG_FILE="$1"
            shift
            ;;
        *)
            echo "❌ 未知选项: $1"
            echo "使用 -h 或 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 检查配置文件
if [[ -z "$CONFIG_FILE" ]]; then
    echo "❌ 错误: 请指定配置文件"
    echo ""
    show_help
    exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "❌ 错误: 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 检查 Python 是否可用
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ 错误: 未找到 Python，请安装 Python 3.9+"
    exit 1
fi

# 构建命令行参数
ARGS="--config \"$CONFIG_FILE\""

if [[ "$REBUILD" == true ]]; then
    ARGS="$ARGS --rebuild"
fi

if [[ "$DRY_RUN" == true ]]; then
    ARGS="$ARGS --dry-run"
fi

if [[ "$VERBOSE" == true ]]; then
    ARGS="$ARGS --verbose"
fi

# 切换到脚本目录执行
cd "$SCRIPT_DIR" || exit 1

# 执行 Python 脚本
echo "🚀 启动视频博客生成器..."
echo ""
eval "$PYTHON_CMD blog_main.py $ARGS"

exit $?
