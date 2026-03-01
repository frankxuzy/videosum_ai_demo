# PRD: 视频查重功能集成

## 现状分析

### 已有功能
代码中已存在基础查重机制：

1. **查重方法** (`src/blog_generator.py:138-140`):
```python
def is_video_processed(self, video_id: str) -> bool:
    """Check if a video has already been processed."""
    return video_id in self.metadata.get_video_ids()
```

2. **仅在 update 模式使用** (`src/blog_generator.py:377-379`):
```python
# Check if already processed (skip in update mode)
if mode == "update" and self.is_video_processed(video_id):
    print(f"  ⏭️  已处理过，跳过")
    continue
```

### 问题
- 普通模式（不带 `--update`）会**重新处理**已存在的视频
- 没有提示用户哪些视频已存在
- `--rebuild` 模式会强制重建，但用户可能想部分更新

---

## 需求方案

### 方案 A: 智能默认模式（推荐）
**描述**: 普通模式下自动检测已处理视频并提示用户

**行为变更**:
| 模式 | 原行为 | 新行为 |
|------|--------|--------|
| 普通模式 | 重新处理所有视频 | 检测已处理视频，提示用户选择 |
| --update | 跳过已处理 | 保持不变 |
| --rebuild | 重新处理所有 | 保持不变 |

**交互流程**:
```
检测到 3 个视频：
  [新] video1 - 未处理
  [已存在] video2 - 2026-02-28 已处理
  [新] video3 - 未处理

选项:
  1. 只处理新视频 (--update 行为)
  2. 重新处理所有视频 (--rebuild 行为)
  3. 选择性处理 (逐个确认)
  4. 取消
```

### 方案 B: 扩展 metadata 校验
**描述**: 除了 video_id，还校验内容是否变化

**新增校验项**:
- 视频标题变更检测
- 字幕内容哈希（可选）
- 处理模式变更（brief/detailed）

**metadata 扩展**:
```json
{
  "video_id": "xxx",
  "processed_at": "2026-02-28 12:55",
  "content_hash": "sha256:abc123...",
  "mode": "detailed",
  "needs_update": false
}
```

### 方案 C: 命令行增强
**描述**: 添加更多查重相关参数

**新增参数**:
```bash
# 只处理新视频（无论是否使用 --update）
python blog_main.py --config videos.yaml --skip-existing

# 显示哪些视频已存在但不处理
python blog_main.py --config videos.yaml --dry-run --check-duplicates

# 强制重新处理特定视频（逗号分隔）
python blog_main.py --config videos.yaml --force-update "video1,video2"
```

---

## 推荐实现

### 第一阶段: 方案 A（核心优化）

修改 `src/blog_generator.py` 的 `process_videos` 方法：

```python
def process_videos(self, videos: List, mode: str = "normal",
                   translate: bool = True) -> int:
    # ... 原有代码 ...

    # 分类视频
    new_videos = []
    existing_videos = []

    for video_config in videos:
        video_id = extract_video_id(video_config.url)
        if self.is_video_processed(video_id):
            existing_videos.append((video_id, video_config))
        else:
            new_videos.append((video_id, video_config))

    # 普通模式下的智能提示
    if mode == "normal" and existing_videos:
        print(f"\n⚠️  检测到 {len(existing_videos)} 个已处理视频:")
        for vid, cfg in existing_videos:
            info = self.get_video_info(vid)
            print(f"   - {vid} (处理于 {info.get('processed_at', 'unknown')})")

        print(f"\n选择操作:")
        print(f"  1. 只处理新视频（{len(new_videos)} 个）")
        print(f"  2. 重新处理所有视频")
        print(f"  3. 取消")

        choice = input("\n请输入选项 (1-3): ").strip()
        if choice == "1":
            videos = [v for _, v in new_videos]
        elif choice == "2":
            pass  # 处理所有
        else:
            print("已取消")
            return 0

    # ... 继续原有处理逻辑 ...
```

### 第二阶段: 方案 C（命令行增强）

在 `blog_main.py` 添加参数：

```python
parser.add_argument(
    '--skip-existing',
    action='store_true',
    help='自动跳过已存在的视频（无需交互）'
)

parser.add_argument(
    '--check-duplicates',
    action='store_true',
    help='只检查重复，不实际处理'
)
```

---

## 文件修改清单

| 文件 | 修改内容 | 优先级 |
|------|----------|--------|
| `src/blog_generator.py` | 添加视频分类逻辑、用户交互提示 | P0 |
| `blog_main.py` | 添加 `--skip-existing`, `--check-duplicates` 参数 | P1 |
| `README.md` | 更新查重功能文档 | P2 |

---

## 验收标准

1. **功能测试**
   - [ ] 普通模式下检测到已处理视频时显示提示
   - [ ] 选项1正确只处理新视频
   - [ ] 选项2正确重新处理所有视频
   - [ ] `--update` 模式保持原有行为
   - [ ] `--rebuild` 模式保持原有行为

2. **边界情况**
   - [ ] 所有视频都已处理时给出友好提示
   - [ ] 没有已处理视频时直接执行
   - [ ] 用户取消时优雅退出

3. **性能**
   - [ ] 查重检查在100个视频时 < 1秒

---

## 替代方案

如果不需要交互式提示，可以简化为：

```python
# 在普通模式下自动采用 update 行为
if mode == "normal":
    mode = "update"  # 自动跳过已存在视频
```

但这会减少灵活性，推荐保留用户选择权。
