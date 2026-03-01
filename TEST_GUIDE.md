# 多语言字幕功能测试指南

本文档说明如何手动测试 `transcript_main.py` 的多语言支持功能。

## 环境准备

```bash
# 1. 确保依赖已安装
pip install -r requirements.txt

# 2. 设置 OpenAI API Key（翻译非中文视频需要）
export OPENAI_API_KEY="your-api-key"
# 或者在 .env 文件中设置
```

## 测试用例

### 测试 1：英语视频（应翻译）

**目的**：验证英语视频能正常获取字幕并翻译

```bash
python transcript_main.py "https://www.youtube.com/watch?v=FiztJuyl7p4" -v
```

**预期输出**：
```
视频 ID: FiztJuyl7p4
--------------------------------------------------
可用的字幕语言:
  - English (en) [自动生成] [将使用]
✓ 成功获取字幕
  语言: English (en)
  段落数: XX
  文本长度: XXXX 字符

正在翻译成中文...
✓ 翻译完成
...
✓ 原文字幕 (en) 已保存: output/FiztJuyl7p4_en.txt
✓ 中文翻译已保存: output/FiztJuyl7p4_zh.txt
```

---

### 测试 2：韩语视频（应翻译）

**目的**：验证非英语视频能自动检测语言并翻译

```bash
python transcript_main.py "https://www.youtube.com/watch?v=9bZkp7q19f0" -v
```

**预期输出**：
```
视频 ID: 9bZkp7q19f0
--------------------------------------------------
可用的字幕语言:
  - Korean (ko) [自动生成] [将使用]
✓ 成功获取字幕
  语言: Korean (ko)
  段落数: XX
  文本长度: XXXX 字符

正在翻译成中文...
✓ 翻译完成
...
✓ 原文字幕 (ko) 已保存: output/9bZkp7q19f0_ko.txt
✓ 中文翻译已保存: output/9bZkp7q19f0_zh.txt
```

---

### 测试 3：中文视频（应跳过翻译）

**目的**：验证中文视频能自动检测并跳过翻译（节省 API 费用）

```bash
# 找一个中文视频，例如某个中文教程
python transcript_main.py "https://www.youtube.com/watch?v=XXXX" -v
```

**预期输出**：
```
视频 ID: XXXX
--------------------------------------------------
可用的字幕语言:
  - Chinese (zh) [自动生成] [将使用]
✓ 成功获取字幕
  语言: Chinese (zh) [中文视频]
  段落数: XX
  文本长度: XXXX 字符

检测到中文视频，跳过翻译
...
✓ 中文字幕已保存: output/XXXX_zh.txt
```

**注意**：中文视频只生成一个 `_zh.txt` 文件，节省翻译费用。

---

### 测试 4：强制指定语言

**目的**：验证 `--language` 参数能强制选择特定语言

```bash
# 在有多个语言字幕的视频上测试
python transcript_main.py "URL" --language en -v
```

**预期输出**：
```
可用的字幕语言:
  - English (en) [自动生成] [将使用]
  - Spanish (es) [自动生成]
✓ 成功获取字幕
  语言: English (en)
...
```

---

### 测试 5：不翻译模式

**目的**：验证 `--no-translate` 只获取原文

```bash
python transcript_main.py "https://www.youtube.com/watch?v=FiztJuyl7p4" --no-translate
```

**预期输出**：
```
✓ 原文字幕 (en) 已保存: output/FiztJuyl7p4_en.txt
```

不会生成 `_zh.txt` 文件。

---

### 测试 6：无字幕视频（应失败）

**目的**：验证无字幕视频给出清晰错误提示

```bash
# 找一个没有字幕的视频
python transcript_main.py "https://www.youtube.com/watch?v=XXXX"
```

**预期输出**：
```
⚠️  视频 XXXX 没有字幕

❌ 无法获取字幕，程序结束
提示: 此视频可能没有字幕，或尝试指定 --language 参数
```

---

## 测试检查清单

| 测试 | 描述 | 状态 |
|------|------|------|
| 1 | 英语视频自动检测并翻译 | ⬜ |
| 2 | 韩语/日语视频自动检测并翻译 | ⬜ |
| 3 | 中文视频跳过翻译（省钱） | ⬜ |
| 4 | `--language` 强制指定语言 | ⬜ |
| 5 | `--no-translate` 只获取原文 | ⬜ |
| 6 | 无字幕视频优雅失败 | ⬜ |

## 常见问题

### Q: 如何找不同语言的视频？

- **英语**: 大多数 YouTube 视频
- **中文**: 搜索 "中文教程"、"科技"、"知识"
- **韩语**: K-pop MV，如 Gangnam Style
- **日语**: 动漫、J-pop
- **德语/法语/西班牙语**: 搜索对应语言关键词

### Q: 如何判断视频是否有字幕？

在 YouTube 播放器上点击 "CC" 按钮查看可用字幕。

### Q: 测试时不想消耗 API 额度？

使用 `--no-translate` 参数，只测试字幕获取功能。

### Q: 测试失败怎么办？

1. 检查网络连接（需要访问 YouTube）
2. 检查 `youtube-transcript-api` 是否最新：`pip install -U youtube-transcript-api`
3. 查看具体错误信息，可能是视频区域限制

## 预期文件输出

测试完成后，`output/` 目录结构应如下：

```
output/
├── {video1}_en.txt      # 英语原文
├── {video1}_zh.txt      # 中文翻译
├── {video2}_ko.txt      # 韩语原文
├── {video2}_zh.txt      # 韩语翻译
├── {video3}_zh.txt      # 中文视频（只有一个文件）
└── ...
```
