"""更新 Markdown 文件中的总结内容"""
import argparse
import re
import sys
from pathlib import Path


def update_markdown(md_path: str, summary: str = None, key_points: list = None):
    """
    更新 Markdown 文件中的总结和关键要点

    Args:
        md_path: Markdown 文件路径
        summary: 中文摘要文本
        key_points: 关键要点列表
    """
    md_file = Path(md_path)
    if not md_file.exists():
        print(f"错误: 文件不存在 {md_path}")
        sys.exit(1)

    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 更新摘要
    if summary:
        # 替换中文摘要部分
        content = re.sub(
            r"(## 中文摘要\n\n)<!-- Claude: 请在此处填写中文摘要 -->\n.*?\n(?=---)",
            rf"\1{summary}\n",
            content,
            flags=re.DOTALL
        )
        print("✓ 已更新中文摘要")

    # 更新关键要点
    if key_points:
        points_text = "\n".join([f"- {point}" for point in key_points])
        content = re.sub(
            r"(## 关键要点\n\n)<!-- Claude: 请在此处填写关键要点 -->\n.*?\n(?=---)",
            rf"\1{points_text}\n",
            content,
            flags=re.DOTALL
        )
        print("✓ 已更新关键要点")

    # 保存更新后的文件
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n已更新: {md_path}")


def main():
    parser = argparse.ArgumentParser(
        description="将 Claude 的总结填入 Markdown 文件"
    )
    parser.add_argument(
        "md_file",
        help="Markdown 文件路径"
    )
    parser.add_argument(
        "-s", "--summary",
        help="中文摘要文本"
    )
    parser.add_argument(
        "-p", "--points",
        nargs="+",
        help="关键要点（可多个）"
    )

    args = parser.parse_args()
    update_markdown(args.md_file, args.summary, args.points)


if __name__ == "__main__":
    main()
