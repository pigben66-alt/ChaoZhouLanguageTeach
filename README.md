# 潮州方言伴学系统 (Teochew Dialect AI Learning System)

基于 **Agent 驱动**的潮州方言伴学网页教育系统，整合 AI 技术与国产大模型服务，面向潮州方言学习者提供个性化、智能化的方言学习体验。

---

## 项目简介

潮州方言（潮州话/潮汕话）是闽南语系的重要分支，拥有悠久的历史和丰富的文化内涵。本系统通过 AI Agent 编排架构，围绕"听—说—读—用"四维能力，为学习者提供从零基础到精通的完整学习路径。

### 核心亮点

- **AI Agent 伴学引擎**：Agent 作为智能中枢，分析用户学习数据，形成个性化教学策略，不仅是学习工具，更是专属方言导师
- **个性化适配**：Agent 根据用户学习数据、能力水平和交互风格，动态调整教学内容、对话语气和推荐策略
- **场景化对话模拟**：20+ 真实生活场景的方言对话练习，独立于 Agent 伴学界面，沉浸式角色扮演
- **国产大模型集成**：支持 DeepSeek、通义千问、智谱 GLM 等多模型路由
- **知识追踪与自适应学习**：基于贝叶斯知识追踪(BKT)和间隔重复(SRS)算法，精准评估掌握度并优化复习计划

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端展示层 (HTML/CSS/JS)                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 学习中心  │ │ Agent对话 │ │ 场景模拟  │ │ 数据看板  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
├─────────────────────────────────────────────────────────────┤
│                    后端服务层 (FastAPI)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 用户认证  │ │ 学习服务  │ │ 数据分析  │ │ 管理后台  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────────────────────────────────────────────┐       │
│  │              AI Agent 编排引擎                     │       │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │       │
│  │  │意图识别│ │记忆管理│ │任务规划│ │工具调用│ │策略决策│   │       │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘   │       │
│  └──────────────────────────────────────────────────┘       │
├─────────────────────────────────────────────────────────────┤
│                    国产大模型接入层                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │ DeepSeek │ │ 通义千问  │ │ 智谱GLM  │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
├─────────────────────────────────────────────────────────────┤
│                    数据持久层                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │PostgreSQL│ │  Redis   │ │ 向量数据库 │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 功能模块

### 用户系统
- 手机号 + 验证码注册/登录
- JWT 双 Token 认证（Access Token + Refresh Token）
- 密码找回与重置
- 用户等级体系（L1-L8）
- 学习档案与进度追踪

### 方言学习
- **发音学习**：18 声母 + 韵母系统 + 8 声调训练，发音评测与纠错
- **词汇学习**：12 大类话题词汇，闪卡模式、听音选义、间隔重复
- **语法讲解**：潮州方言特殊语法点，与普通话对比展示
- **场景对话**：20+ 生活场景模拟，引导模式 + 自由模式

### AI Agent 伴学
- 意图识别与智能路由
- 短期/长期记忆管理
- 任务规划与工具调用
- 个性化学习建议与激励
- 薄弱点分析与强化推荐

### 数据分析
- 学习日历热力图
- 六维能力雷达图
- 词汇量增长曲线
- 声调准确率分布
- 学习时段分析

### 管理后台
- 用户管理
- 内容管理（词汇/语法/场景）
- 数据统计仪表盘
- 系统配置

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | HTML5 + CSS3 + JavaScript (原生) |
| 后端 | Python 3.11+ / FastAPI |
| 数据库 | PostgreSQL 16 + Redis 7 |
| ORM | SQLAlchemy 2.0 (异步) |
| 认证 | JWT (python-jose) + bcrypt |
| 实时通信 | WebSocket |
| 任务队列 | Celery + Redis |
| 大模型 | DeepSeek / 通义千问 / 智谱 GLM |
| 容器化 | Docker + Docker Compose |

---

## 快速开始

### 环境要求

- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- Docker & Docker Compose（推荐）

### 使用 Docker 启动（推荐）

```bash
# 克隆项目
git clone https://github.com/your-username/teochew-learning.git
cd teochew-learning

# 启动所有服务
docker compose up -d

# 初始化数据库
docker compose exec backend alembic upgrade head

# 导入种子数据
docker compose exec backend python seed_data.py
```

启动后访问：
- 前端页面：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`
- 管理后台：`http://localhost:8000/api/v1/admin/dashboard`

### 本地开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（复制并编辑 .env 文件）
cp .env.example .env

# 确保 PostgreSQL 和 Redis 已启动
# 初始化数据库
alembic upgrade head

# 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 环境变量配置

编辑 `backend/.env` 文件：

```env
APP_NAME=潮州方言伴学系统
APP_VERSION=1.0.0
DEBUG=true

DATABASE_URL=postgresql+asyncpg://teochew:teochew123@localhost:5432/teochew_learning
REDIS_URL=redis://localhost:6379/0

JWT_SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=120

DEEPSEEK_API_KEY=your_deepseek_api_key
QWEN_API_KEY=your_qwen_api_key
GLM_API_KEY=your_glm_api_key
```

---

## 项目结构

```
teochew-learning/
├── index.html                    # 前端主页面
├── docker-compose.yml            # Docker 编排配置
├── README.md
├── 潮州方言伴学系统_架构设计框架.md  # 架构设计文档
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    ├── alembic.ini
    ├── seed_data.py              # 种子数据脚本
    ├── admin.html                # 管理后台页面
    ├── .env                      # 环境变量配置
    ├── alembic/                  # 数据库迁移
    └── app/
        ├── main.py               # 应用入口
        ├── config.py             # 配置管理
        ├── database.py           # 数据库连接
        ├── tasks.py              # Celery 任务
        ├── api/                  # API 路由
        │   ├── auth.py           # 认证接口
        │   ├── learning.py       # 学习接口
        │   ├── agent.py          # Agent 接口
        │   ├── analytics.py      # 数据分析接口
        │   ├── admin.py          # 管理后台接口
        │   └── websocket.py      # WebSocket 接口
        ├── models/               # 数据模型
        ├── schemas/              # Pydantic 模型
        ├── services/             # 业务逻辑
        │   ├── user_service.py
        │   ├── learning_service.py
        │   ├── agent_service.py
        │   ├── analytics_service.py
        │   └── admin_service.py
        ├── agent/                # Agent 引擎
        │   ├── engine.py
        │   ├── memory.py
        │   └── toolbox.py
        ├── llm/                  # 大模型适配
        │   ├── router.py
        │   └── adapters/
        ├── middleware/           # 中间件
        │   ├── auth.py
        │   └── security.py
        └── utils/                # 工具函数
            ├── cache.py
            ├── security.py
            └── helpers.py
```

---

## API 接口概览

| 模块 | 前缀 | 说明 |
|------|------|------|
| 认证 | `/api/v1/auth` | 注册、登录、密码重置、Token 刷新 |
| 用户 | `/api/v1/users` | 个人信息、学习档案、能力评估 |
| 学习 | `/api/v1/learning` | 知识点、词汇、发音评测、学习记录 |
| Agent | `/api/v1/agent` | Agent 对话、场景模拟、学习建议 |
| 分析 | `/api/v1/analytics` | 学习统计、数据看板 |
| 管理 | `/api/v1/admin` | 用户管理、内容管理、系统配置 |
| WebSocket | `/ws` | 实时数据推送 |

---

## 潮州方言能力等级

| 等级 | 词汇量 | 发音准确率 | 水平描述 |
|------|--------|-----------|---------|
| L1 启蒙 | 0-100 | ≥30% | 零基础入门 |
| L2 初识 | 100-300 | ≥45% | 能说日常称谓 |
| L3 入门 | 300-600 | ≥55% | 能进行基本问候 |
| L4 初级 | 600-1000 | ≥65% | 能应对日常生活 |
| L5 中级 | 1000-1500 | ≥75% | 能与母语者日常交流 |
| L6 进阶 | 1500-2200 | ≥85% | 能讨论抽象话题 |
| L7 高级 | 2200-3000 | ≥92% | 接近母语者 |
| L8 精通 | 3000+ | ≥96% | 掌握俗语/谚语/文化 |

---

## 许可证

MIT License

---

## 联系方式

如有问题或建议，欢迎提交 Issue 或 Pull Request。
