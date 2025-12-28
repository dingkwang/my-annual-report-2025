# OpenAI Conversation Diary Generator

将你的 OpenAI 对话记录转换成每日日记，采用完全累积上下文模式（类似 podcastify）。

## 特性

- 🤖 使用 LangChain 结构化输出（Pydantic 模型）
- 📝 生成客观流水账风格的日记
- 🔄 完全累积上下文模式 - 每天的日记都能"看到"之前所有的日记
- 📁 按年份组织输出文件
- 💾 支持断点续传
- 🧪 完整的测试覆盖

## 安装

1. 安装依赖（推荐使用 uv）：
```bash
uv pip install -r requirements.txt
```

2. 配置 LLM（编辑 `config.yaml`）：
```yaml
llm:
  model: "grok-4-1-fast-non-reasoning"
  base_url: "YOUR_BASE_URL_HERE"  # 替换为你的 API endpoint
  api_key: "YOUR_API_KEY_HERE"    # 替换为你的 API key
```

## 使用方法

### 基本使用

```bash
# 生成所有日记
python generate_diary.py

# 指定输入文件
python generate_diary.py --input conversations_by_date.json

# 测试模式（只处理前3天）
python generate_diary.py --test
```

### 测试

```bash
# 使用 pytest
uv run -m pytest test_diary_generator.py -v

# 或直接运行测试文件
python test_diary_generator.py
```

## 输出格式

生成的日记保存在 `output/diaries/` 目录下，按年份组织：

```
output/diaries/
├── 2023/
│   ➥── 2023-01-08.md
│   ├── 2023-01-09.md
│   └── ...
├── 2024/
│   └── ...
└── 2025/
    └── ...
```

每个日记文件格式：

```markdown
# 技术学习的一天

**日期**: 2023-01-08

今天主要和 ChatGPT 讨论了机器学习相关的内容。上午9点多，我询问了 RLHF（人类反馈强化学习）的三个阶段具体是什么...
```

## 工作原理

1. **数据加载**：读取 `conversations_by_date.json`
2. **顺序处理**：按日期从早到晚处理
3. **上下文累积**：每生成一天的日记，都会累积到上下文中
4. **结构化输出**：使用 LangChain 的 `with_structured_output` 生成 `DayDiary(title, content)`
5. **文件保存**：按年份组织保存 markdown 文件

## 与 Podcastify 的相似性

- ✅ 都是按顺序处理内容块（podcastify 按 chunk，我们按天）
- ✅ 都累积**生成的内容**而非原始输入
- ✅ 都通过上下文注入保持连贯性
- ✅ 都使用结构化输出确保格式一致

## 配置选项

`config.yaml` 中的主要配置：

- `llm.temperature`: 控制生成的随机性（默认 0.3）
- `diary_settings.min_conversation_length`: 过滤过短对话（默认 50 字符）
- `output.base_dir`: 输出目录
- `logging.level`: 日志级别

## 断点续传

程序会自动保存进度到 `progress.json`，如果中断可以继续运行，已处理的日期会被跳过。

## 注意事项

- 确保有足够的 API 配额（696 天约需要 696 次 API 调用）
- 2M 上下文窗口足够存储所有日记（每篇 200-500 字）
- 首次运行建议使用 `--test` 模式验证配置