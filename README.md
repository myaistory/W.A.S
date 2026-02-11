# Walnut-AI-Support (W.A.S.) 🌰

**W.A.S.** 是一款专为核桃编程（Walnut Programming）设计的智能技术支持系统。它基于 FastAPI 构建，通过集成 Groq (Llama 3.3) 大模型和 RAG（检索增强生成）技术，为老师提供 7x24 小时的金牌级技术支持响应。

## 🚀 核心特性

- **高效推理**：集成 Groq Llama-3.3-70b 模型，提供极速的语义理解与回复。
- **智能 RAG (P2)**：基于向量检索（Semantic Search）的知识库引擎，精准匹配核桃内部 SOP。
- **多轮会话 (P3)**：具备 30 分钟窗口期的短程记忆，支持上下文关联问答。
- **异步处理**：采用 `BackgroundTasks` 机制，秒回飞书回调，彻底解决超时重试问题。
- **健壮监控 (P0/P1)**：
    - 结构化滚动日志记录 (`logs/was.log`)。
    - 实时健康检查端点 (`/health`)，监控 Groq API 及知识库状态。

## 🛠️ 技术栈

- **Framework**: FastAPI (Python 3.11+)
- **LLM Engine**: Groq (Llama-3.3-70b-versatile)
- **Data Science**: Numpy (Vector computing)
- **Messaging**: Feishu (ByteDance Lark) API
- **DevOps**: Systemd, Git, Virtualenv

## 📂 目录结构

```text
.
├── core/
│   ├── server.py           # FastAPI 服务入口 & 飞书协议处理
│   ├── rag_engine.py       # AI 推理核心逻辑
│   ├── vector_engine.py    # 语义检索实现 (P2)
│   ├── session_manager.py  # 会话记忆管理 (P3)
│   └── logger.py           # 结构化日志模块 (P0)
├── data/
│   ├── walnut_kb.json      # 核心知识库 (SOP/FAQ)
│   └── vector_store.db     # 向量缓存数据库
├── logs/                   # 服务运行日志
└── infra/                  # 基础设施脚本与辅助工具
```

## ⚙️ 快速开始

### 1. 环境准备
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量 (`.env`)
```env
FEISHU_APP_ID=your_id
FEISHU_APP_SECRET=your_secret
GROQ_API_KEY=your_key
```

### 3. 运行服务
```bash
nohup python core/server.py > was.log 2>&1 &
```

## 📊 状态看板
- **Webhook**: `http://<ip>:8001/event`
- **Health**: `http://<ip>:8001/health`

## 🛡️ 安全说明
本项目已通过 `.gitignore` 自动过滤所有敏感 Key 及环境配置文件。请确保在生产环境中妥善保管 `.env` 文件。

---
**Maintained by Random (💀) @ OpenClaw**
