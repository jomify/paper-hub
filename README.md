# Paper Hub

本地运行的 AI 论文管理与阅读工作台。

它把论文导入、元数据整理、应用内 PDF 阅读、页级翻译、论文 Digest、知识地图、主题发现下载整合在一个单机 Web 应用里，适合个人研究者在本地管理论文库。

## 功能概览

- 本地 SQLite 持久化，数据默认保存在项目目录
- 导入本地 PDF，自动提取标题、摘要、标签、封面
- 应用内阅读 PDF，并记录阅读进度
- AI 整理论文元数据：中文标题、摘要、标签、分类、合集
- 页级中文阅读、嵌入翻译、全文翻译任务
- 论文 Digest：Abstract / Method / Conclusion 精读摘要
- 全库知识地图：思维导图 + 知识图谱
- 主题发现：按输入主题检索开放 PDF、AI 评价 CRAAP、推荐阅读顺序并自动导入
- 可切换多种 AI Provider，包括 OpenAI 兼容端点、本地 Ollama、LM Studio 等

## 技术栈

- 前端：原生 `HTML + CSS + JavaScript`
- 后端：Python 标准库 `http.server`
- 数据库：SQLite
- PDF 处理：`PyMuPDF (fitz)`、`pypdf`
- AI 调用：通过后端统一适配多种 Provider HTTP API

## 项目结构

```text
paper-hub/
├─ index.html                # 页面骨架
├─ app.js                    # 前端状态、渲染、交互、API 调用
├─ styles.css                # 样式
├─ server.py                 # 后端 API、数据库、PDF、AI、任务调度
├─ start.bat                 # Windows 一键启动
├─ .env.example              # 环境变量示例
├─ provider_config.json      # Provider 配置文件（公开仓库中应保持无密钥）
├─ paper_hub.db              # 运行后生成的本地数据库
└─ storage/                  # PDF、封面、渲染图、翻译缓存、digest、地图缓存
```

## 环境要求

- Python 3.10+
- 已安装依赖：
  - `PyMuPDF`
  - `pypdf`

如果你使用全新环境，推荐先手动安装：

```powershell
pip install pymupdf pypdf
```

## 配置教程

### 1. 准备环境变量

复制示例文件：

```powershell
Copy-Item .env.example .env
```

然后按需填写：

```env
AI_PROVIDER=openai
AI_API_KEY=你的_API_Key
AI_MODEL=gpt-5-mini
AI_API_URL=
```

说明：

- `AI_PROVIDER`：当前默认 Provider 标识
- `AI_API_KEY`：对应 Provider 的密钥
- `AI_MODEL`：模型名
- `AI_API_URL`：可选，自定义兼容端点时填写

如果你不想直接写 `.env`，也可以启动应用后，在页面右上角的 `AI Provider` 对话框里配置。

### 2. Provider 配置方式

项目支持两种配置来源：

1. `.env`
2. 应用内 `AI Provider` 面板

应用内保存的配置会写入 `provider_config.json`。公开仓库里不要提交真实 API key。

### 3. 公开仓库前的安全建议

发布到 GitHub 前，至少确认这些文件不含真实数据：

- `.env`
- `provider_config.json`
- `paper_hub.db`
- `storage/` 下的 PDF、渲染图、翻译缓存、digest、知识地图缓存

推荐做法：

- 只提交 `.env.example`
- `provider_config.json` 保持空 key
- 不提交本地数据库和论文文件
- 用 `.gitignore` 忽略运行时文件

## 使用教程

### 启动

方式 1：

```powershell
python server.py
```

方式 2（Windows）：

```text
start.bat
```

浏览器打开：

```text
http://127.0.0.1:8876
```

### 基础使用

#### 1. 新增论文

- 点击 `新增论文`
- 手动填写标题、作者、年份、标签、摘要等信息
- 保存后进入论文库

#### 2. 导入本地 PDF

- 点击 `导入 PDF`
- 选择本地文件
- 系统会自动提取标题、摘要、标签，并生成封面

#### 3. AI 整理

- 在右侧论文详情面板选中某篇论文
- 点击 `AI 整理`
- 系统会补全中文标题、中文摘要、关键词、分类、合集、优先级等

#### 4. 阅读 PDF

- 选中带本地 PDF 的论文
- 点击 `在应用内阅读`
- 可切换：
  - 原文
  - 中文精读
  - 嵌入翻译

#### 5. 查看论文 Digest

- 在详情面板点击 `查看`
- 或在阅读器里点击 `论文精华`
- 系统会整理 `Abstract / Method / Conclusion`

#### 6. 查看知识地图

- 点击 `知识地图`
- 支持：
  - 全库视角
  - 当前论文视角
  - 思维导图
  - 知识图谱

#### 7. 主题发现

- 点击 `主题发现`
- 输入主题，例如：
  - `RAG evaluation`
  - `multimodal retrieval`
  - `多模态检索增强生成`
- 设置：
  - 检索篇数
  - 自动下载前 N 篇
- 系统会：
  - 检索开放 PDF
  - 用 AI 做 CRAAP 评价
  - 给出推荐阅读顺序
  - 自动下载推荐 PDF 并导入本地论文库

说明：

- 主题发现默认使用开放可下载 PDF 的 arXiv 结果
- 如果配置了 AI，会优先做语义相关性评价，不要求标题逐字匹配
- 如果 AI 不可用，会回退到本地启发式评分

## 数据位置

- 数据库：`paper_hub.db`
- PDF：`storage/pdfs/`
- 封面：`storage/covers/`
- 阅读器渲染图：`storage/renders/`
- 翻译缓存：`storage/translations/`
- Digest 缓存：`storage/digests/`
- 知识地图缓存：`storage/maps/`

## 常见问题

### 1. 为什么打开 `index.html` 没反应？

这是一个本地 HTTP 应用，不支持直接双击 HTML 文件。请先运行：

```powershell
python server.py
```

### 2. 为什么 AI 功能不可用？

常见原因：

- 没配置 API key
- Provider 端点不对
- 模型名不对
- 网络不可达

先检查 `.env` 或应用内 `AI Provider` 面板。

### 3. 为什么中文主题发现效果一般？

如果没有配置 AI，系统无法先把中文主题改写成更适合学术检索的英文查询，召回效果会变差。建议：

- 配置 AI Provider
- 或者直接输入英文研究主题

## 发布到 GitHub 的建议流程

```powershell
git status
git add .
git commit -m "Prepare public release"
git push origin main
```

在这之前，请确认：

- 没有真实 API key
- 没有个人论文 PDF
- 没有本地数据库内容
- 没有翻译缓存、渲染图、digest 缓存

## License

如果准备公开发布，建议补充 `LICENSE` 文件后再推送。
