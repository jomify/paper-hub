# Paper Hub

本地论文管理系统。

当前版本支持：

- SQLite 数据库，保存在项目目录下的 `paper_hub.db`
- PDF 导入，文件保存在 `storage/pdfs/`
- 上传 PDF 后自动提取标题、封面和标签
- 配置 `OPENAI_API_KEY` 后可使用真实 AI 生成标题、中文翻译、摘要、标签和分类
- 在应用内直接阅读 PDF，并记录阅读页码
- 新增 / 编辑 / 删除论文
- 收藏、合集、标签、笔记
- 封面墙 / 列表视图切换

## 启动

```powershell
cd E:\workspace\paper-hub
python server.py
```

或者直接双击：

```text
start.bat
```

浏览器打开：

```text
http://127.0.0.1:8876
```

如果要启用真实 AI，直接编辑项目目录下的 `.env`：

```env
AI_PROVIDER=glm
AI_API_KEY=你的 GLM Key
AI_MODEL=glm-5
```

保存后重新启动：

```powershell
python server.py
```

## 数据位置

- 数据库：`paper_hub.db`
- PDF 文件：`storage/pdfs/`

都在项目目录下面。
