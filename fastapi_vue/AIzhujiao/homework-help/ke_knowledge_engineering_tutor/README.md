# 知识工程课程多模态智能助教系统

这是一个面向 **北京科技大学计算机系研究生《知识工程》课程** 的多模态智能助教原型系统。

## 功能概览

### 1. 课程题目解答页
- 支持同时输入多个题目文本
- 支持拖拽上传多张题目图片
- 支持一张图片中包含多个题目时，由模型自动拆分并分别解答
- 支持按题目切换查看解析结果
- 预置“知识表示 / 知识图谱 / 推理 / 语义检索 / 大模型与知识工程 / 作业辅导”等课程导向 Prompt

### 2. PPT 知识点总结页
- 支持上传 `.pptx`
- 自动抽取每页文本内容
- 自动总结本页重点、全局知识点、易混概念、建议复习问题
- 适合做课前预习、课后复习和汇报展示

## 安装依赖
```bash
python -m venv .venv
# PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 配置环境变量
将 `.env.example` 复制为 `.env`，并填写新的 API Key：
```bash
copy .env.example .env
```

```env
ARK_API_KEY=你的新key
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL=doubao-seed-2-0-pro-260215
```

## 启动
```bash
python -m uvicorn app.main:app --reload
```
打开：
```text
http://127.0.0.1:8000
```

## 页面说明
- `/`：批量查题与多模态解答
- `/ppt-summary`：PPT 知识点总结

## 适合汇报时的系统描述
本系统聚焦《知识工程》课程场景，支持批量题目输入、题图自动拆题和面向研究生课程的专业化解答；同时提供 PPT 知识点总结页面，可对课程讲义进行章节级知识抽取与复习建议生成，形成“题目辅导 + 课件总结”双页面智能助教原型。
