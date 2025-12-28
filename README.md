# 📔 ChatGPT 日记生成器 | Diary Generator

从 ChatGPT 对话记录自动生成个人日记和年度总结

Generate personal diaries and annual summaries from your ChatGPT conversation history.

---

## 🌟 特性 Features

✅ 自动从 ChatGPT 对话生成每日日记  
✅ 生成年度总结（基于全年日记）  
✅ 支持多种 LLM 模型（OpenRouter, OpenAI 等）  
✅ **双模式**：Web 界面 或 命令行工具  
✅ 快速模式（测试用）和完整模式  
✅ 可自定义个人简历背景  
✅ 支持断点续传（命令行模式）  

---

## 📦 准备工作

### 1. 安装依赖

```bash
# 确保已安装 uv (https://docs.astral.sh/uv/)
uv sync
```

### 2. 导出 ChatGPT 对话数据

1. 登录 [ChatGPT](https://chatgpt.com)
2. 点击左下角头像 → **Settings** → **Data controls**
3. 点击 **Export data**
4. 等待邮件通知（通常几分钟到几小时）
5. 下载 ZIP 文件

### 3. 获取 API Key

推荐使用 [OpenRouter](https://openrouter.ai)（有免费模型）：

1. 注册 OpenRouter 账号
2. 获取 API Key
3. 选择模型（推荐免费模型）：
   - `nvidia/nemotron-3-nano-30b-a3bfree` (免费)
   - `openai/gpt-4o-mini`
   - 更多模型：https://openrouter.ai/models

---

## 🚀 使用方式

> 💡 **快速开始**: 如果你想要最快速度上手，请查看 [5 分钟快速指南](QUICK_START.md)

### 方式一：Web 界面（推荐，适合新手）

#### 启动服务

```bash
# 方法 1: 使用启动脚本
./start_web.sh

# 方法 2: 手动启动
uv run python web_app.py
```

#### 使用界面

1. **打开浏览器**: http://localhost:5000

2. **配置 LLM**:
   ```
   Model:    nvidia/nemotron-3-nano-30b-a3bfree
   Base URL: https://openrouter.ai/api/v1
   API Key:  your-api-key-here
   ```

3. **可选：填写个人简历**
   - 点击展开"个人简历"部分
   - 按年份填写职业经历

4. **上传 ZIP 文件**
   - 选择从 ChatGPT 导出的 ZIP 文件
   - 支持最大 500MB

5. **选择模式**
   - **快速模式**：每年前 10 篇（适合测试）
   - **完整模式**：生成所有日记

6. **开始生成**
   - 点击"开始生成日记"
   - 等待完成
   - 查看生成的日记列表

#### Web 界面特点

- ✅ 无需编辑配置文件
- ✅ 实时查看生成结果
- ✅ 下载所有日记为 ZIP
- ✅ 友好的错误提示
- ❌ 不支持断点续传

📖 **详细文档**: [README_web.md](README_web.md)

---

### 方式二：命令行（推荐，适合批量处理）

#### 1. 配置文件

```bash
# 复制示例配置
cp config.example.yaml config.yaml

# 编辑配置文件
nano config.yaml  # 或使用你喜欢的编辑器
```

配置内容：

```yaml
llm:
  model: "nvidia/nemotron-3-nano-30b-a3bfree"
  base_url: "https://openrouter.ai/api/v1"
  api_key: "your-api-key-here"
  temperature: 0.3

output:
  base_dir: "output/diaries"

diary_settings:
  min_conversation_length: 10

# 可选：个人简历
_annual_resume:
  2021_and_before: "2020年毕业于XX大学计算机专业"
  2022: "2022年加入XX公司担任软件工程师"
  2023: "..."
  2024: "..."
  2025: "..."
```

#### 2. 运行命令

```bash
# 快速模式（测试用，每年前 10 篇）
uv run generate_diary.py your_export.zip --quick

# 完整模式（生成所有日记）
uv run generate_diary.py your_export.zip

# 覆盖已生成的日记
uv run generate_diary.py your_export.zip --overwrite

# 使用自定义配置文件
uv run generate_diary.py your_export.zip --config custom_config.yaml
```

#### 命令行特点

- ✅ 支持断点续传（通过 `progress.json`）
- ✅ 更适合自动化和批处理
- ✅ 可以方便地集成到脚本中
- ✅ 性能更好（无 Web 开销）
- ❌ 需要手动编辑配置文件

📖 **详细文档**: [README_diary_generator.md](README_diary_generator.md)

---

## 📊 生成结果

### 目录结构

```
output/
├── diaries/              # 命令行生成的日记
│   ├── 2023/
│   │   ├── 2023-01-08-今日纠正地址误差记录.md
│   │   ├── 2023-01-10-JSON库学习与面试准备.md
│   │   └── 2023-年度总结.md
│   ├── 2024/
│   │   └── ...
│   └── 2025/
│       └── ...
└── web_sessions/         # Web 界面生成的日记
    └── {session_id}/
        └── diaries/
            └── ...
```

### 每日日记示例

```markdown
# 实现C++kd-tree最近邻搜索

**日期**: 2023-02-04

今天主要在研究和实现kd-tree的最近邻搜索算法。
上午花了一些时间理解kd-tree的数据结构原理...
```

### 年度总结示例

```markdown
# 2023年度总结

**年份**: 2023

回顾2023年，这是充满挑战和成长的一年。
在技术上，我深入学习了...
```

---

## 🔧 常见问题

### 1. 文件上传失败 - 413 错误

**问题**: ZIP 文件太大

**解决方案**:
- Web 界面支持最大 500MB
- 如果更大，请使用命令行工具

### 2. API 调用失败

**问题**: 生成失败，提示 API 错误

**检查**:
- API Key 是否正确
- Base URL 格式（需要包含 `/v1`）
- 网络连接是否正常

**测试 API**:
```bash
curl -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"nvidia/nemotron-3-nano-30b-a3bfree","messages":[{"role":"user","content":"Hi"}]}'
```

### 3. 年度总结为空或内容少

**原因**: 在快速模式下，每年只生成 10 篇日记，内容可能不够丰富

**解决方案**:
- 使用完整模式生成所有日记
- 年度总结会基于所有已生成的日记

### 4. 生成速度慢

**说明**: 每篇日记需要调用 LLM API，速度取决于：
- 模型响应速度
- 对话数量
- 网络延迟

**优化**:
- 先用快速模式测试（2-5 分钟）
- 选择更快的模型
- 使用命令行工具（支持断点续传）

### 5. 如何继续未完成的生成？

**命令行**:
```bash
# 直接运行，会自动跳过已生成的日记
uv run generate_diary.py your_export.zip
```

**Web 界面**:
- 目前不支持，建议使用命令行

📖 **更多故障排除**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 📈 使用建议

### 首次使用流程

1. **测试阶段**（推荐 Web 界面）
   ```
   使用快速模式 → 生成 30 篇日记（每年10篇）→ 检查质量
   ```

2. **调整配置**
   - 如果效果不理想，调整 model 或 temperature
   - 可以添加个人简历背景

3. **完整生成**（推荐命令行）
   ```bash
   uv run generate_diary.py your_export.zip
   ```

4. **查看结果**
   - 检查 `output/diaries/` 目录
   - 阅读年度总结

### 最佳实践

✅ **首次使用**: Web 界面 + 快速模式  
✅ **批量处理**: 命令行 + 完整模式  
✅ **定期更新**: 命令行（支持增量生成）  
✅ **实验不同模型**: Web 界面（无需修改配置文件）  

---

## 🎯 对比：Web vs 命令行

| 特性 | Web 界面 | 命令行 |
|------|----------|--------|
| 易用性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 配置方式 | 表单填写 | 编辑 YAML |
| 断点续传 | ❌ | ✅ |
| 实时查看 | ✅ | ❌ |
| 下载结果 | ZIP 下载 | 本地目录 |
| 批量处理 | ❌ | ✅ |
| 自动化 | ❌ | ✅ |
| 文件大小限制 | 500MB | 无限制 |
| 适用场景 | 测试、尝试 | 生产、批量 |

---

## 🛠️ 技术栈

- **后端**: Python 3.13+ / Flask
- **前端**: HTML + CSS + JavaScript (原生)
- **AI**: LangChain + OpenAI-compatible APIs
- **包管理**: uv

---

## 📚 文档索引

- **[5分钟快速开始](QUICK_START.md)** - 最快上手指南 ⚡
- [Web 界面详细文档](README_web.md) - 浏览器使用说明
- [命令行详细文档](README_diary_generator.md) - 批量处理指南
- [快速使用指南](QUICK_RUN_USAGE.md) - 原有的快速指南
- [故障排除](TROUBLESHOOTING.md) - 常见问题解决

---

## 🤝 贡献 Contributing

欢迎提交 Issue 和 Pull Request！

---

## 📄 License

MIT

---

## 🙏 致谢

- OpenAI ChatGPT
- LangChain
- OpenRouter
- uv Package Manager

---

**享受你的 AI 驱动的个人日记之旅！✨**
