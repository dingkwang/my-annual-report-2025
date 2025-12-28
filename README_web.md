# Web 界面使用指南 | Web Interface Guide

ChatGPT 日记生成器 - Web 版

通过浏览器界面轻松生成你的个人日记，无需命令行操作！

> 💡 **提示**: 如果你需要批量处理或自动化，请参考 [命令行文档](README_diary_generator.md)

---

## 🚀 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 启动服务

**方式一：使用启动脚本**（推荐）

```bash
./start_web.sh
```

**方式二：手动启动**

```bash
uv run python web_app.py
```

### 3. 打开浏览器

访问: **http://localhost:5000**

---

## 📖 详细使用说明

### 第一步：LLM 模型配置

填写 LLM API 配置信息：

| 字段 | 说明 | 示例值 |
|------|------|--------|
| **Model** | 模型名称 | `nvidia/nemotron-3-nano-30b-a3bfree` |
| **Base URL** | API 端点 | `https://openrouter.ai/api/v1` |
| **API Key** | 你的 API 密钥 | `sk-or-v1-...` |
| **Temperature** | 生成随机性 (0-2) | `0.3` |

**推荐模型**:
- `nvidia/nemotron-3-nano-30b-a3bfree` - 免费，速度快
- `openai/gpt-4o-mini` - 质量高，付费
- `google/gemini-flash-1.5` - 免费，效果好

更多模型: https://openrouter.ai/models

### 第二步：个人简历（可选）

点击"📝 个人简历（可选）"展开：

- 按年份填写你的职业经历
- 帮助 AI 生成更贴合你背景的日记
- 如果留空，将自动生成通用简历

**示例**:
```
2021及之前: 2020年毕业于XX大学计算机专业，主修人工智能
2022: 加入XX公司担任算法工程师，从事计算机视觉研究
2023: 转向大模型方向，参与LLM应用开发
```

### 第三步：上传 ZIP 文件

1. 点击文件上传区域
2. 选择从 ChatGPT 导出的 ZIP 文件
3. 确认文件大小 < 500MB
4. 看到 ✓ 文件已选择

**注意**:
- ZIP 文件必须包含 `conversations.json`
- 不要解压后重新压缩
- 上传前会显示文件大小

### 第四步：选择生成模式

**快速模式**（推荐首次使用）:
- 每年生成前 10 篇日记
- 总共约 30 篇（如果有 3 年数据）
- 用时: 2-5 分钟
- 适合: 测试效果、快速预览

**完整模式**:
- 生成所有对话的日记
- 数量取决于对话记录
- 用时: 10 分钟 - 数小时
- 适合: 完整记录、最终生成

### 第五步：开始生成

1. 点击"🚀 开始生成日记"按钮
2. 看到加载动画和进度提示
3. 等待生成完成
4. 查看生成结果列表

### 第六步：查看和下载

**查看日记**:
- 点击任意日记标题
- 在新标签页打开查看
- 支持 Markdown 格式

**下载所有日记**:
- 点击"📥 下载所有日记"按钮
- 获得 ZIP 压缩包
- 包含所有生成的 Markdown 文件

### 功能特性 Features

- ✅ Web 界面配置，无需修改配置文件
- ✅ 支持自定义 LLM 模型和 API
- ✅ 可选的个人简历集成
- ✅ 实时查看生成的日记
- ✅ 下载所有日记为 ZIP 文件
- ✅ 每日日记和年度总结
- ✅ 快速模式和完整模式

### 导出 ChatGPT 对话数据 Export ChatGPT Conversations

1. 登录 ChatGPT
2. 点击左下角头像 → Settings → Data controls
3. 点击 "Export data"
4. 等待邮件通知
5. 下载 ZIP 文件

## 技术栈 Tech Stack

- **后端**: Flask + Python
- **前端**: HTML + CSS + JavaScript (原生)
- **AI**: LangChain + OpenAI-compatible APIs

## 注意事项 Notes

- 首次使用建议选择"快速模式"测试效果
- API Key 不会被保存到服务器
- 生成的日记保存在 `output/web_sessions/` 目录
- 每个会话有独立的 session_id

## 故障排除 Troubleshooting

### 无法启动服务

```bash
# 检查端口占用
lsof -i :5000

# 使用其他端口
# 修改 web_app.py 中的 port=5000
```

### ZIP 文件上传失败

- 确保 ZIP 文件包含 `conversations.json`
- 检查文件大小是否超过 100MB

### API 调用失败

- 检查 API Key 是否正确
- 确认 Base URL 格式正确
- 查看终端日志了解详细错误

## 开发 Development

```bash
# 开发模式（自动重载）
FLASK_ENV=development uv run python web_app.py
```

## License

MIT

