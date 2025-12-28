# 命令行使用指南 | Command Line Guide

ChatGPT 日记生成器 - 命令行版

通过命令行批量处理你的对话记录，支持断点续传和自动化。

> 💡 **提示**: 如果你想要图形界面，请参考 [Web 界面文档](README_web.md)

---

## 🚀 快速开始

### 1. 准备配置文件

```bash
# 复制示例配置
cp config.example.yaml config.yaml

# 编辑配置文件
nano config.yaml  # 或使用你喜欢的编辑器
```

### 2. 配置 LLM

编辑 `config.yaml`:

```yaml
llm:
  model: "nvidia/nemotron-3-nano-30b-a3bfree"
  base_url: "https://openrouter.ai/api/v1"
  api_key: "your-api-key-here"  # 替换为你的真实 API Key
  temperature: 0.3

output:
  base_dir: "output/diaries"

diary_settings:
  min_conversation_length: 10

logging:
  level: "INFO"
  file: "log/diary_generation.log"

# 可选：个人简历
_annual_resume:
  2021_and_before: "2020年毕业于XX大学计算机专业"
  2022: "2022年加入XX公司担任软件工程师"
  2023: "2023年转向大模型方向"
  2024: "2024年..."
  2025: "2025年..."
```

### 3. 运行生成

```bash
# 快速模式（测试用，每年前10篇）
uv run generate_diary.py your_export.zip --quick

# 完整模式（生成所有日记）
uv run generate_diary.py your_export.zip

# 覆盖模式（重新生成所有）
uv run generate_diary.py your_export.zip --overwrite
```

---

## 📖 详细使用说明

### 命令行参数

```bash
uv run generate_diary.py [ZIP_FILE] [OPTIONS]
```

**位置参数**:
- `ZIP_FILE`: ChatGPT 导出的 ZIP 文件路径

**可选参数**:
- `--config PATH`: 指定配置文件（默认: `config.yaml`）
- `--test`: 测试模式，只处理前 3 天
- `--quick`: 快速模式，每年前 10 篇
- `--overwrite`: 覆盖已生成的日记

### 使用示例

#### 1. 首次使用（推荐快速模式）

```bash
# 测试配置和效果
uv run generate_diary.py my_conversations.zip --quick
```

输出:
```
📦 Extracting conversations from ZIP file...
✅ Extracted conversations.json
📊 Parsing conversations and grouping by date...
Found 1745 conversations
✅ Created conversations_by_date.json with 696 dates
🚀 Initializing Diary Generator...

⚡ Running in quick mode (first 10 diaries per year)...
📅 Preparing to generate diaries for 30 days...
Generating diaries: 100%|████████████| 30/30 [02:15<00:00]

✅ Diary generation complete! Generated 30 diaries.
📖 Generating annual summary for 2023...
✅ Annual summary for 2023 completed!
```

#### 2. 完整生成

```bash
# 生成所有日记
uv run generate_diary.py my_conversations.zip
```

特点:
- 自动跳过已生成的日记（通过 `progress.json`）
- 可以随时中断，下次继续
- 生成年度总结

#### 3. 重新生成

```bash
# 忽略进度，重新生成所有
uv run generate_diary.py my_conversations.zip --overwrite
```

#### 4. 使用自定义配置

```bash
# 为不同项目使用不同配置
uv run generate_diary.py data.zip --config work_config.yaml
uv run generate_diary.py data.zip --config personal_config.yaml
```

---

## 📁 输出结构

### 目录组织

```
output/diaries/
├── 2023/
│   ├── 2023-01-08-今日纠正地址误差记录.md
│   ├── 2023-01-10-JSON库学习与面试准备.md
│   ├── 2023-02-04-实现C++kd-tree最近邻搜索.md
│   └── 2023-年度总结.md
├── 2024/
│   ├── 2024-01-01-命名规范与代码格式化探讨.md
│   └── 2024-年度总结.md
└── 2025/
    ├── 2025-01-03-ViLD模型概述与个人思考的.md
    └── 2025-年度总结.md
```

### 文件命名

- 每日日记: `YYYY-MM-DD-标题.md`
- 年度总结: `YYYY-年度总结.md`

### 日记格式

```markdown
# 实现C++kd-tree最近邻搜索

**日期**: 2023-02-04

今天主要在研究和实现kd-tree的最近邻搜索算法。
上午花了一些时间理解kd-tree的数据结构原理，
这是一种用于多维空间搜索的二叉树结构...
```

---

## 🔧 高级功能

### 断点续传

程序自动保存进度到 `progress.json`:

```json
{
  "processed_dates": [
    "2023-01-08",
    "2023-01-10",
    ...
  ],
  "last_processed": "2023-02-07",
  "last_updated": "2025-12-28T10:30:00"
}
```

**使用方式**:
- 运行被中断后，直接再次运行相同命令
- 程序会自动跳过已处理的日期
- 不需要手动管理进度

**重置进度**:
```bash
# 删除进度文件，重新开始
rm progress.json
uv run generate_diary.py data.zip
```

### 个人简历集成

在 `config.yaml` 中配置 `_annual_resume`:

```yaml
_annual_resume:
  2021_and_before: "2020年毕业于清华大学计算机系，本科期间主修人工智能"
  2022: "2022年加入字节跳动担任算法工程师，从事推荐系统研发"
  2023: "2023年转向大模型方向，参与公司LLM应用开发"
  2024: "2024年晋升为高级工程师，负责RAG系统架构"
  2025: "2025年开始探索AI Agent应用"
```

**作用**:
- 生成的日记会更贴合你的职业背景
- AI 能更好地理解你的技术水平和关注点
- 年度总结会结合简历信息

**自动生成**:
- 如果留空，首次运行时会自动生成
- 基于 `example_diary.json` 中的 `resume_plain_text`

### 日志管理

配置日志输出:

```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "log/diary_generation.log"
```

查看日志:
```bash
# 实时查看
tail -f log/diary_generation.log

# 搜索错误
grep ERROR log/diary_generation.log

# 查看特定日期
grep "2023-01-08" log/diary_generation.log
```

---

## ⚙️ 配置说明

### LLM 配置

```yaml
llm:
  model: "nvidia/nemotron-3-nano-30b-a3bfree"
  base_url: "https://openrouter.ai/api/v1"
  api_key: "sk-or-v1-..."
  temperature: 0.3
```

**推荐模型**:

| 模型 | 特点 | 价格 | 速度 |
|------|------|------|------|
| `nvidia/nemotron-3-nano-30b-a3bfree` | 免费，效果好 | 免费 | 快 |
| `openai/gpt-4o-mini` | 质量高 | $$ | 中 |
| `anthropic/claude-3-haiku` | 平衡 | $ | 快 |
| `google/gemini-flash-1.5` | 免费，长上下文 | 免费 | 快 |

**Temperature 说明**:
- `0.0`: 最确定性，重复性高
- `0.3`: 推荐值，平衡创造性和一致性
- `0.7`: 更有创造性
- `1.0`: 高随机性

### 输出配置

```yaml
output:
  base_dir: "output/diaries"  # 输出目录
```

多项目管理:
```yaml
# work_config.yaml
output:
  base_dir: "output/work_diaries"

# personal_config.yaml
output:
  base_dir: "output/personal_diaries"
```

### 日记设置

```yaml
diary_settings:
  min_conversation_length: 10  # 最短对话长度（字符数）
```

- 太小: 会包含很多无意义的短对话
- 太大: 可能过滤掉有价值的简短对话
- 推荐: `10-50`

---

## 🎯 工作流程示例

### 场景 1: 首次生成

```bash
# 1. 配置
cp config.example.yaml config.yaml
nano config.yaml  # 填写 API Key

# 2. 测试
uv run generate_diary.py my_export.zip --quick

# 3. 检查结果
ls output/diaries/2023/
cat output/diaries/2023/2023-年度总结.md

# 4. 满意后完整生成
uv run generate_diary.py my_export.zip
```

### 场景 2: 定期更新

```bash
# 每月更新一次
# 1. 下载最新的 ChatGPT 导出
# 2. 运行生成（自动跳过已有的）
uv run generate_diary.py latest_export.zip

# 只会生成新增的日记
```

### 场景 3: 批量实验

```bash
# 尝试不同模型
for model in "nvidia/nemotron-3-nano-30b-a3bfree" "openai/gpt-4o-mini"; do
  echo "Testing $model..."
  # 创建配置文件
  sed "s/model: .*/model: \"$model\"/" config.yaml > test_config.yaml
  # 运行测试
  uv run generate_diary.py data.zip --config test_config.yaml --quick
done
```

---

## 🔍 故障排除

### API 调用失败

**错误**: `HTTP Request: POST ... "HTTP/1.1 401 Unauthorized"`

**解决**:
```bash
# 测试 API Key
curl -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"nvidia/nemotron-3-nano-30b-a3bfree","messages":[{"role":"user","content":"test"}]}'
```

### 进度文件损坏

```bash
# 删除并重新开始
rm progress.json
uv run generate_diary.py data.zip
```

### 内存不足

**症状**: 程序崩溃，系统卡顿

**原因**: ZIP 文件太大或对话太多

**解决**:
```bash
# 使用快速模式减少处理量
uv run generate_diary.py data.zip --quick

# 或分批处理（手动编辑 conversations_by_date.json）
```

---

## 📊 性能参考

| 数据规模 | 快速模式 | 完整模式 |
|----------|----------|----------|
| 1 年数据 (~200 对话) | 1-2 分钟 | 5-10 分钟 |
| 2 年数据 (~400 对话) | 2-3 分钟 | 10-20 分钟 |
| 3 年数据 (~600 对话) | 3-5 分钟 | 15-30 分钟 |

*基于 nvidia/nemotron-3-nano-30b-a3bfree 模型的测试结果*

---

## 🤝 与 Web 界面对比

| 特性 | 命令行 | Web 界面 |
|------|--------|----------|
| 断点续传 | ✅ | ❌ |
| 自动化 | ✅ | ❌ |
| 批量处理 | ✅ | ❌ |
| 易用性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 配置灵活性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 文件大小限制 | 无限制 | 500MB |

---

## 📚 相关文档

- [主文档](README.md)
- [Web 界面文档](README_web.md)
- [快速使用指南](QUICK_RUN_USAGE.md)
- [故障排除](TROUBLESHOOTING.md)

---

**享受命令行的强大功能！💪**
