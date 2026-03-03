# AI 求职助手

[English README](README.md)

一个端到端的 AI 求职系统，能够自动抓取招聘信息、通过多阶段流水线将职位与简历匹配、生成定制简历和求职信、提供技能市场分析报告，并通过人机协同审批自动填写申请表。同时支持**英文**和**中文**求职市场。

使用 **Gemini 3.1 Pro** 处理低成本任务（解析、提取），使用 **Claude Sonnet 4.6** 处理推理任务（评分、求职信、浏览器代理）。嵌入向量通过 **Gemini embedding-001** 生成。匹配流水线包括启发式预过滤、向量检索、交叉编码器重排序、LLM 快速评分和全维度 LLM-as-Judge 评估。

## 系统架构

```
                                                                              定制
简历上传 ──► 抓取职位 ──► 预过滤 ──► 匹配评分 ──► 报告 ──► 简历生成 ──► 自动填表
                  │           │           │           │          │            │
         英文流水线:      资历/         ChromaDB +   Jinja2 HTML  外部         LangGraph
           JSearch API   地点/类型    FlashRank +   + Claude    微服务       代理 +
           Greenhouse    启发式       快速评分 +    求职信      (LangGraph   interrupt()
           Lever                     Claude 全                 LaTeX→PDF)  人工审核
           Adzuna                    LLM-as-Judge
           Arbeitnow                       │
           RemoteOK                  技能分析
           WeWorkRemotely             (频率分析
                  │                  共现分析
         中文流水线:                  PDF报告)
           腾讯招聘
           网易招聘           自动检测     jieba ATS +
           MokaHR            语言 →      FlashRank
           阿里巴巴                       多语言 /
           京东校招                       BGE 重排序
           BOSS直聘 (浏览器)
           智联招聘 (浏览器)
           51job (浏览器)
           拉勾网 (浏览器)
           字节跳动
```

### 模型路由

| 任务 | 模型 | 原因 |
|------|------|------|
| 简历/职位解析、关键词提取 | `gemini-3.1-pro-preview` | 最新推理模型，性价比高 |
| 嵌入向量生成 | `gemini-embedding-001` | 灵活维度，MRL |
| 快速评分相关性预筛选 | `claude-sonnet-4-6` | 快速候选分流 |
| 全量匹配评分 (LLM-as-Judge) | `claude-sonnet-4-6` | 卓越的多维推理能力 |
| 求职信生成 | `claude-sonnet-4-6` | 自然、定制化的写作 |
| 浏览器代理推理 | `claude-sonnet-4-6` | 复杂表单填写的决策能力 |

### 匹配流水线（5 阶段）

```
原始职位 ──► 预过滤 ──► 嵌入索引 ──► 检索 ──► 快速评分 ──► 全量评分
  200        ↓ 35       ChromaDB     ↓ 30      ↓ 25        ↓ 25
             资历       Gemini       向量相似度  Claude JSON  Claude
             地点       批量嵌入     + FlashRank 相关性      结构化
             类型                    重排序      1-10 分流    输出
```

1. **预过滤** — `JobPreFilter` 通过快速启发式规则移除明显不相关的职位：
   - 资历级别匹配（例如 "mid" 用户会排除 VP/总监/首席等职位）
   - 地点兼容性（国家关键词重叠；远程岗位始终通过）
   - 雇佣类型过滤（全职/兼职/合同制标准化）
2. **向量相似度** — 通过余弦相似度从 ChromaDB 中检索 Top-30 候选（使用聚焦检索查询：目标职位 + 技能 + 地点，而非原始简历）
3. **交叉编码器重排序** — FlashRank 缩减至 Top-10（本地 CPU，免费）。中文简历自动选择 FlashRank 多语言版或 BGE 重排序器。
4. **快速评分** — Claude 通过轻量提示评定相关性 1-10 分（500字符职位摘要，JSON 响应）。低于阈值 4 的职位被跳过。
5. **全量 LLM-as-Judge 评分** — Claude 对剩余候选在技能/经验/学历/地点/薪资维度上评分（每项 1-10），使用 `MatchingWeights` 配置中的显式权重百分比。返回结构化输出，包含评分理由、优势、缺失技能和面试要点。

**中文流水线自动检测：** 当简历为中文时，`ats_mode=auto` 自动选择基于 jieba 的 ATS 关键词评分（英文用正则），`reranker_mode=auto` 自动选择 BGE 重排序器（英文用 FlashRank）。

## 项目结构

```
AI_Agent_Job_Application/
├── backend/                             # Python 3.13 + FastAPI
│   ├── app/
│   │   ├── main.py                      # FastAPI 入口 + 中间件
│   │   ├── config.py                    # 双层配置（环境变量 + YAML）
│   │   ├── core/
│   │   │   ├── auth.py                  # API Key 认证（X-API-Key 头）
│   │   │   ├── utils.py                 # 工具函数（SQL LIKE 转义）
│   │   │   └── rate_limit.py            # SlowAPI 限流器
│   │   ├── db/
│   │   │   └── session.py               # 单例异步引擎 + 会话工厂
│   │   ├── models/                      # SQLAlchemy ORM（8 张表）
│   │   ├── schemas/                     # 请求/响应模型，分页
│   │   ├── routers/                     # API 路由（7 个模块）
│   │   ├── services/                    # 业务逻辑层
│   │   │   ├── matching/                # 匹配流水线（预过滤、嵌入、检索、评分、ATS、技能提取）
│   │   │   ├── scraping/               # 18 个抓取器（英文 + 中文）
│   │   │   ├── analysis/               # 技能市场分析
│   │   │   ├── agent/                  # LangGraph 浏览器代理
│   │   │   ├── reports/                # PDF/HTML 报告 + 技能分析报告
│   │   │   └── resume_generator/       # 简历生成微服务客户端
│   │   ├── mcp/                         # FastMCP 服务器
│   │   └── worker/                      # ARQ 后台任务
│   ├── tests/                           # 692 后端 + 42 前端 = 734 总测试数
│   └── alembic/                         # 数据库迁移（3 个版本）
├── frontend/                            # React 19 + TypeScript + Vite 7
│   ├── src/
│   │   ├── pages/                       # 仪表盘、设置、技能分析
│   │   ├── components/                  # UI 组件（含错误边界）
│   │   ├── stores/                      # Zustand 状态管理
│   │   ├── hooks/                       # TanStack Query + WebSocket
│   │   └── api/                         # HTTP 客户端（含 API Key 认证）
│   └── __tests__/                       # 42 个 Vitest 测试
├── docker-compose.yml                   # 6 个服务
├── .github/workflows/ci.yml            # 3 阶段 CI
└── .env.example                         # 环境变量模板
```

---

## 安装指南

### 环境要求

| 工具 | 版本 | 用途 |
|------|------|------|
| Python | 3.13+ | 后端 |
| [uv](https://docs.astral.sh/uv/) | 最新版 | Python 包管理器 |
| Node.js | 22+ | 前端 |
| Docker & Docker Compose | 最新版 | 完整部署（或手动运行 Postgres/Redis） |

### 第一步：克隆并配置环境

```bash
git clone <repo-url>
cd AI_Agent_Job_Application
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API 密钥。详见下方 [API 密钥](#api-密钥env) 章节。

### 第二步：后端安装

```bash
cd backend
uv sync --dev
```

此命令会安装所有 Python 依赖，包括 jieba（中文NLP）、FlagEmbedding（BGE 重排序器）、Playwright 等。

**安装 Playwright 浏览器**（浏览器抓取器和应用代理需要）：

```bash
uv run playwright install chromium
```

### 第三步：数据库设置

**方案 A：Docker（推荐）**
```bash
# 在项目根目录 — 只启动 Postgres + Redis
docker compose up -d db redis
```

**方案 B：本地安装**
- 安装 PostgreSQL 16，创建名为 `job_agent` 的数据库，用户 `postgres`/`postgres`
- 安装 Redis 7，使用默认端口 6379

**运行数据库迁移：**
```bash
cd backend
uv run alembic upgrade head
```

迁移包含 3 个版本：
1. 初始表结构（users, jobs, match_results, applications, cover_letters, agent_logs）
2. `generated_resumes` 表（简历生成器追踪）
3. `job_skills` 表（技能市场分析）

### 第四步：前端安装

```bash
cd frontend
npm install
```

### 第五步：简历生成器设置（可选）

定制简历生成功能使用一个外部微服务，运行 LangGraph 多代理流水线生成基于 LaTeX 的 PDF。此功能为可选项 — 所有其他功能无需此服务即可正常工作。

**方案 A：Docker（通过 `docker compose up` 自动启动）**

`resume-generator` 服务已包含在 `docker-compose.yml` 中，会自动构建并启动。

**方案 B：本地运行**

```bash
# 将简历生成器项目克隆到本项目旁边
cd ../Resume_and_Cover_Letter_Generator/self_use/resume-generator/backend
uv sync
uv run uvicorn main:app --port 48765
```

然后在 `.env` 中设置：
```env
RESUME_GENERATOR_URL=http://localhost:48765
```

**需求：** 简历生成器需要安装 LaTeX 发行版（TeX Live 或 MiKTeX）用于 PDF 编译。

### 第六步：开发模式运行

```bash
# 终端 1：后端 API
cd backend
uv run uvicorn app.main:app --reload --port 8000

# 终端 2：前端开发服务器
cd frontend
npm run dev

# 终端 3（可选）：简历生成器
cd ../Resume_and_Cover_Letter_Generator/self_use/resume-generator/backend
uv run uvicorn main:app --port 48765
```

打开 http://localhost:5173 访问仪表盘。API 文档：http://localhost:8000/docs。

### 第七步：Docker 全栈运行

```bash
docker compose up -d
```

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:3000 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| 简历生成器 | http://localhost:48765 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

### 第八步：运行测试

```bash
# 后端单元测试（692 个测试，无需外部 API）
cd backend
uv run pytest --ignore=tests/e2e_pipeline_test.py --ignore=tests/test_integration/ -q

# 前端测试（42 个测试）
cd frontend
npx vitest run
```

---

## 配置说明

### API 密钥（`.env`）

| 环境变量 | 是否必需？ | 获取方式 | 功能说明 |
|----------|-----------|----------|----------|
| `GOOGLE_API_KEY` | **必需** | [Google AI Studio](https://aistudio.google.com/apikey) | Gemini LLM（解析、提取）+ 嵌入生成。**没有此密钥系统无法运行。** |
| `ANTHROPIC_API_KEY` | **必需**（或使用代理） | [Anthropic Console](https://console.anthropic.com/) | Claude 评分、求职信、浏览器代理。如使用本地代理，设置 `ANTHROPIC_BASE_URL`。 |
| `JSEARCH_API_KEY` | 可选 | [RapidAPI JSearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) | JSearch 抓取器（聚合 LinkedIn、Indeed、Glassdoor）。免费额度：100 次/月。 |
| `ADZUNA_APP_ID` | 可选 | [Adzuna Developer](https://developer.adzuna.com/) | Adzuna 招聘板抓取器。有免费额度。 |
| `ADZUNA_APP_KEY` | 可选 | 同上 | 与 `ADZUNA_APP_ID` 配合使用。 |
| `LANGSMITH_API_KEY` | 可选 | [LangSmith](https://smith.langchain.com/) | LLM 调用追踪与调试。正常使用不需要。 |

**使用 Claude 代理**（如 [claude-code-proxy](https://github.com/nicobailon/claude-code-proxy)）：

```env
ANTHROPIC_BASE_URL=http://localhost:42069
ANTHROPIC_API_KEY=proxy-no-key-needed
```

### 安全配置（`.env`）

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `API_KEY` | _(空 = 关闭认证)_ | 设置一个密钥字符串，敏感接口（代理、配置、抓取、匹配）将要求 `X-API-Key` 请求头。留空为开发模式。 |
| `CORS_ORIGINS` | `["http://localhost:5173","http://localhost:3000"]` | 允许的 CORS 源列表。 |

当设置了 `API_KEY` 时，前端也需要配置。在前端 `.env` 中添加：
```env
VITE_API_KEY=your-secret-api-key-here
```

### 完整 `.env` 参考

```env
# ── 必需 ──────────────────────────────────────────────────────────────
GOOGLE_API_KEY=your-google-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# ── 数据库与队列（默认值与 docker-compose 一致）──────────────────────
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/job_agent
REDIS_URL=redis://localhost:6379/0

# ── 可选 API 密钥 ─────────────────────────────────────────────────────
JSEARCH_API_KEY=your-rapidapi-key-here
ADZUNA_APP_ID=your-adzuna-app-id
ADZUNA_APP_KEY=your-adzuna-app-key

# ── 模型配置（显示默认值）─────────────────────────────────────────────
GEMINI_MODEL=gemini-3.1-pro-preview
CLAUDE_MODEL=claude-sonnet-4-6
EMBEDDING_MODEL=gemini-embedding-001

# ── Claude 代理（可选）────────────────────────────────────────────────
# ANTHROPIC_BASE_URL=http://localhost:42069

# ── 安全 ──────────────────────────────────────────────────────────────
# API_KEY=your-secret-api-key-here
# CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# ── 可观测性（可选）───────────────────────────────────────────────────
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=your-langsmith-key-here
LANGSMITH_PROJECT=job-application-agent

# ── 简历生成器（可选外部微服务）───────────────────────────────────────
# RESUME_GENERATOR_URL=http://localhost:48765
```

### 用户偏好设置（`backend/data/user_config.yaml`）

通过 Pydantic 验证的偏好设置，控制求职搜索、匹配权重和抓取器配置。可通过 `PUT /api/config/preferences` 接口或直接编辑 YAML 文件修改。

<details>
<summary>英文求职配置示例</summary>

```yaml
job_titles:
  - Software Engineer
  - AI Engineer
  - Full-stack Developer
locations:
  - Remote
  - United States
  - Canada
salary_min: 100000
salary_max: 200000
salary_currency: USD
workplace_types: [remote, hybrid]
experience_level: mid             # entry | mid | senior | lead | executive
employment_types: [FULLTIME]      # FULLTIME | PARTTIME | CONTRACT | INTERNSHIP
date_posted: month                # today | 3days | week | month | all

# 评分权重（必须合计为 1.0）
weights:
  skills: 0.35
  experience: 0.25
  education: 0.15
  location: 0.15
  salary: 0.10

# 使用的抓取源
enabled_sources:
  - arbeitnow
  - greenhouse
  - lever
final_results_count: 10
num_pages_per_source: 5

greenhouse_board_tokens: [stripe, cloudflare, figma, airbnb]
lever_companies: [netflix, rippling]
```
</details>

<details>
<summary>中文求职配置示例</summary>

```yaml
job_titles:
  - 软件工程师
  - AI工程师
  - 全栈开发工程师
locations: [北京, 上海, 深圳, 杭州, 远程]
salary_min: 300000
salary_max: 600000
salary_currency: CNY
workplace_types: [remote, hybrid, onsite]
experience_level: mid

# 中文流水线设置
ats_mode: auto                    # auto = 中文用jieba，英文用正则
reranker_mode: flashrank-multilingual  # 或 'bge'（1GB下载）或 'auto'
recruitment_type: social          # social（社招）| campus（校招）| both

# 中文抓取源
enabled_sources:
  - tencent
  - netease
  - bytedance
  - jd_campus

# 需要手动配置的源（详见抓取器设置指南）
# mokahr_org_ids: [org-id-1, org-id-2]
# alibaba_app_key: your-alibaba-key
# boss_zhipin_cookie: your-session-cookie
```
</details>

---

## 抓取器设置指南

并非所有抓取器都能开箱即用。下表列出了每个数据源的需求。

### 无需配置（立即可用）

这些抓取器使用完全公开的 API，无需任何配置：

| 数据源 | 市场 | 说明 |
|--------|------|------|
| `arbeitnow` | 全球/英文 | 公开 REST API |
| `remoteok` | 全球/英文 | 公开 JSON API，仅远程岗位 |
| `weworkremotely` | 全球/英文 | RSS 订阅源 |
| `tencent` | 中国 | 腾讯招聘公开 API |
| `netease` | 中国 | 网易招聘公开 API |
| `jd_campus` | 中国 | 京东校招公开 API（仅校招/实习） |
| `bytedance` | 中国 | 字节跳动公开 API |

### 需要 API 密钥（`.env` 文件）

| 数据源 | 配置项 | 获取方式 | 免费额度？ |
|--------|--------|----------|------------|
| `jsearch` | `JSEARCH_API_KEY` | [RapidAPI JSearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) | 是（100次/月） |
| `adzuna` | `ADZUNA_APP_ID` + `ADZUNA_APP_KEY` | [Adzuna Developer](https://developer.adzuna.com/) | 是 |

### 需要公司列表（`user_config.yaml`）

| 数据源 | 配置项 | 如何获取 |
|--------|--------|----------|
| `greenhouse` | `greenhouse_board_tokens` | 访问 `boards.greenhouse.io/{token}`，token 即 board slug。示例：`stripe`, `cloudflare` |
| `lever` | `lever_companies` | 访问 `jobs.lever.co/{company}`，company 即公司 slug。示例：`netflix`, `rippling` |
| `workday` | `workday_urls` | 找到公司的 Workday 招聘页面 URL |
| `mokahr` | `mokahr_org_ids` | 在公司招聘页的网络请求中查找 org ID |

### 需要手动凭证（`user_config.yaml`）

| 数据源 | 配置项 | 设置方式 |
|--------|--------|----------|
| `alibaba` | `alibaba_app_key` | 在[阿里巴巴开放平台](https://open.alibaba.com/)注册，创建应用，复制 app key。 |
| `boss_zhipin` | `boss_zhipin_cookie` | 1. 在浏览器打开 [BOSS直聘](https://www.zhipin.com/) 并登录。2. 打开 DevTools (F12) → Network → 复制任意请求的 Cookie 头。3. 粘贴到 `user_config.yaml`。**会定期过期，需刷新。** |

### 脆弱 / 反爬（谨慎使用）

| 数据源 | 问题 | 应对方案 |
|--------|------|----------|
| `zhaopin` | 基于会话的内部 API，可能需要有效 cookies | 可能需要浏览器 cookie 注入；可靠性不稳定 |
| `job51` | 薪资文本使用字体混淆（自定义 TTF 字体） | 内置 fonttools 解码器处理，但 51job 更换字体后可能失效 |
| `lagou` | 激进的反爬策略（限速、验证码） | 内置会话管理，但大量使用可能被封 |

### 浏览器抓取器（Playwright）

需先运行 `uv run playwright install chromium`。

| 数据源 | 使用场景 |
|--------|----------|
| `generic` | 没有专用抓取器的招聘页面的通用方案 |
| `workday` | Workday 托管的招聘页面（需配置 `workday_urls`） |

---

## API 接口

### 职位

| 方法 | 路径 | 描述 |
|------|------|------|
| `GET` | `/api/jobs` | 获取职位列表（分页，可按地点/来源/搜索过滤） |
| `GET` | `/api/jobs/{id}` | 获取职位详情 |
| `POST` | `/api/jobs/scrape` | 触发后台抓取（限速 10次/分钟） |
| `GET` | `/api/jobs/scrape/{task_id}/status` | 查询抓取任务进度 |

### 匹配

| 方法 | 路径 | 描述 |
|------|------|------|
| `GET` | `/api/matches` | 获取评分匹配列表（可按关键词/地点/工作类型/最低分过滤） |
| `GET` | `/api/matches/{id}` | 匹配详情（评分细分、优势、差距） |
| `POST` | `/api/matches/run` | 触发匹配流水线后台任务 |
| `POST` | `/api/matches/{id}/rescore` | 重新评分某个匹配 |

### 浏览器代理

| 方法 | 路径 | 描述 |
|------|------|------|
| `POST` | `/api/agent/start` | 为某职位启动浏览器代理（限速 10次/分钟） |
| `POST` | `/api/agent/resume/{thread_id}` | 恢复中断的代理（批准/拒绝/编辑） |
| `WS` | `/ws/agent-status` | 通过 WebSocket 实时获取代理进度 |

### 报告

| 方法 | 路径 | 描述 |
|------|------|------|
| `POST` | `/api/reports/generate` | 为某匹配生成 PDF/HTML 报告 |
| `GET` | `/api/reports/{id}/download` | 下载生成的报告（路径穿越防护） |
| `POST` | `/api/reports/cover-letter` | 生成个性化求职信 |

### 简历生成（定制简历）

| 方法 | 路径 | 描述 |
|------|------|------|
| `GET` | `/api/resumes/health` | 检查简历生成服务可用性 |
| `POST` | `/api/resumes/generate` | 为某匹配生成定制简历+求职信 |
| `GET` | `/api/resumes/{id}/status` | 查询生成状态（完成后自动下载 PDF） |
| `GET` | `/api/resumes/{id}/download/resume` | 下载生成的简历 PDF |
| `GET` | `/api/resumes/{id}/download/cover-letter` | 下载生成的求职信 PDF |
| `GET` | `/api/resumes/by-match/{match_id}` | 列出某匹配的所有生成简历 |

### 技能市场分析

| 方法 | 路径 | 描述 |
|------|------|------|
| `GET` | `/api/skill-analysis/title-groups` | 获取可用的职位标题组及职位数量 |
| `POST` | `/api/skill-analysis/frequencies` | 某职位标题的技能频率分析 |
| `POST` | `/api/skill-analysis/co-occurrences` | 某技能的共现分析 |
| `POST` | `/api/skill-analysis/report` | 完整技能市场分析报告（JSON） |
| `POST` | `/api/skill-analysis/report/pdf` | 生成 PDF/HTML 技能分析报告 |
| `POST` | `/api/skill-analysis/backfill` | 为现有无技能提取的职位补充提取 |

### 配置

| 方法 | 路径 | 描述 |
|------|------|------|
| `GET` | `/api/config/preferences` | 获取当前用户偏好（敏感字段已脱敏） |
| `PUT` | `/api/config/preferences` | 更新偏好设置（验证权重总和） |
| `POST` | `/api/config/resume` | 上传简历（multipart 文件，最大 10 MB） |
| `POST` | `/api/config/linkedin-profile` | 上传 LinkedIn PDF 导出进行解析 |

### 系统

| 方法 | 路径 | 描述 |
|------|------|------|
| `GET` | `/health` | 健康检查（含数据库 + Redis 状态，用于 Docker HEALTHCHECK） |

## 浏览器代理

基于 LangGraph 的浏览器代理处理求职申请表自动填写，支持人机协同审批：

```
开始 → 检测ATS → [路由]
  ├─ Greenhouse/Lever → API直接提交 → 结束（无需浏览器）
  └─ Workday/通用 → 导航 → 填写字段 → 上传简历 → 回答问题
                       → 审核节点（中断：人工审批）
                         ├─ 批准 → 提交 → 结束
                         ├─ 拒绝 → 中止 → 结束
                         └─ 编辑 → 填写字段（循环）
```

代理在 `review_node` 处使用 LangGraph 的 `interrupt()` 暂停，保存状态，在仪表盘中展示已填字段和截图供人工审核后再提交。进度更新通过 WebSocket 实时推送。

## 技能市场分析

技能分析模块从职位中提取技能并提供市场洞察：

- **自动提取** — 抓取时自动从新职位中提取技能（增量处理，仅新职位）
- **补充提取** — `POST /api/skill-analysis/backfill` 处理现有未提取技能的职位
- **频率分析** — 查看某职位标题中最常出现的技能
- **共现分析** — 发现哪些技能经常同时出现
- **PDF 报告** — 使用 Jinja2 + WeasyPrint 生成可下载的技能市场报告
- **前端仪表盘** — 交互式技能分析页面，路由 `/skill-analysis`

## 后台任务

ARQ（异步 Redis 队列）处理长时间运行的任务，API 立即返回：

| 任务 | 触发方式 | 描述 |
|------|----------|------|
| `run_scraping` | `POST /api/jobs/scrape` | 执行所有启用的抓取器，去重，索引到 ChromaDB，自动提取技能 |
| `run_matching` | `POST /api/matches/run` | 预过滤 → 嵌入 → 检索 → 快速评分 → 全量评分 |
| `run_agent` | `POST /api/agent/start` | 启动 LangGraph 浏览器代理工作流 |

Worker 配置：
- **max_tries**: 3（失败任务最多重试 3 次）
- **retry_delay**: 30 秒重试间隔
- **job_timeout**: 600 秒（10 分钟）
- **max_jobs**: 5 个并发任务

## 数据库表结构

8 张表，使用 SQLAlchemy 2.0 异步 ORM + Alembic 迁移管理：

| 表名 | 用途 | 关键列 |
|------|------|--------|
| `users` | 用户资料 | resume_text, email, name |
| `jobs` | 标准化职位 | title, company, source, external_id（唯一对）, description, salary, location |
| `match_results` | 评分结果 | user_id → jobs FK, overall_score, breakdown (JSON), reasoning, strengths, missing_skills |
| `applications` | 已提交申请 | match_id FK, status (pending/submitted/rejected), submitted_at |
| `cover_letters` | 生成的求职信 | match_id FK, content, model_used |
| `generated_resumes` | 简历生成追踪 | match_id FK, external_task_id, status, resume_pdf_path, cover_letter_pdf_path |
| `job_skills` | 提取的技能 | job_id FK, skill_name, category (technical/soft_skill) |
| `agent_logs` | 浏览器代理日志 | thread_id, step, action, screenshot_path, timestamp |

## 测试

### 测试概览

| 测试套件 | 测试数 | 描述 |
|----------|-------:|------|
| 匹配（阶段1） | 73 | 预过滤、嵌入、检索、评分、ATS、流水线 |
| 抓取（阶段2） | 56 | 18个抓取器、去重、标准化、编排 |
| 数据库与API（阶段3） | 47 | 模型、路由、WebSocket、ARQ任务 |
| 浏览器代理（阶段4） | 71 | 状态、图路由、字段映射、ATS策略、中断恢复 |
| 报告（阶段6） | 52 | PDF生成、求职信、模板、评估指标 |
| MCP（阶段7） | 22 | 工具、资源、提示词 |
| Docker（阶段7） | 21 | Compose验证、镜像构建 |
| 配置 | 16 | Settings、UserConfig、MatchingWeights验证 |
| 简历生成 | 54 | 客户端、路由测试 |
| 中文流水线 | 256 | 中文NLP、jieba ATS、BGE/多语言重排序、10个抓取器 |
| 技能市场分析 | 40 | 提取器、持久化、频率、共现、报告、路由 |
| 改进冲刺 | 137 | 认证、路径穿越、上传限制、健康检查、过滤、错误边界 |
| 集成测试 | 44 | 完整用户工作流（11步）、E2E API |
| 前端 | 42 | 组件、状态、hooks |
| **总计** | **734** | **692 后端 + 42 前端** |

### 运行测试

```bash
# 全部后端单元测试（无需外部 API）
cd backend
uv run pytest --ignore=tests/e2e_pipeline_test.py --ignore=tests/test_integration/ -q

# 完整后端测试（含需要数据库/API 的集成测试）
uv run pytest -v

# 特定模块
uv run pytest tests/test_matching/ -v        # 匹配流水线
uv run pytest tests/test_scraping/ -v        # 抓取器
uv run pytest tests/test_agent/ -v           # 浏览器代理
uv run pytest tests/test_reports/ -v         # 报告 + 求职信
uv run pytest tests/test_api/ -v             # API 路由
uv run pytest tests/test_analysis/ -v        # 技能市场分析
uv run pytest tests/test_core/ -v            # 认证 + 工具函数

# 前端
cd frontend
npx vitest run
```

### E2E 流水线测试

`e2e_pipeline_test.py` 针对实际 API 运行完整流水线，覆盖英文和中文求职市场。需要在 `localhost:42069` 运行 Claude 代理，以及有效的 Google API 密钥。

```bash
cd backend
uv run python tests/e2e_pipeline_test.py
```

**阶段 A（英文）：** 从 Arbeitnow、Greenhouse（20个公司）、Lever（4个公司）抓取 3 个职位（Software Engineer, AI Engineer, Full-stack Developer）。使用 Claude 评分，输出报告。

**阶段 B（中文）：** 从腾讯、网易抓取 3 个职位（软件工程师、AI工程师、全栈开发工程师）。自动检测中文简历，使用 jieba ATS 评分和 FlashRank 多语言重排序器。

## 开发历程

本项目按阶段增量构建：

| 阶段 | 描述 | 新增测试 |
|------|------|:--------:|
| 阶段1 — 核心AI | 5阶段匹配流水线（预过滤、嵌入、重排序、LLM评分） | 55 |
| 阶段2 — 抓取 | 8个英文抓取器 | 56 |
| 阶段3 — 数据库与API | PostgreSQL ORM、FastAPI路由、WebSocket、ARQ | 47 |
| 阶段4 — 浏览器代理 | LangGraph状态机、ATS策略、人机协同中断 | 71 |
| 阶段5 — React仪表盘 | React 19 + TanStack Query + Zustand + Recharts | 42 |
| 中文流水线 | 10个中文抓取器、jieba ATS、BGE重排序、多语言嵌入 | 256 |
| 简历生成器 | 外部微服务集成、数据库追踪、前端UI | 73 |
| 技能市场分析 | 技能提取、频率/共现分析、PDF报告、仪表盘 | 40 |
| 改进冲刺 | 6个冲刺共43项改进：安全、可靠性、前端完善、清理 | 137 |

### 改进冲刺详情

全面代码审查发现 43 项改进，分 6 个冲刺实施：

1. **关键后端修复** — 数据库引擎单例（连接池复用）、增量技能提取、路径穿越防护、敏感字段脱敏、可配置 `data_dir`
2. **前端功能修复** — 设置页连通 API、简历上传功能、匹配列表过滤器、共现下钻修复、404 兜底路由
3. **安全加固** — API Key 认证（`X-API-Key` 头）、SQL LIKE 通配符转义、可配置 CORS、10MB 上传限制
4. **可靠性与弹性** — 匹配触发和重评端点实现、httpx 持久连接、有意义的健康检查（DB + Redis）、Worker 重试（max_tries=3）
5. **测试加固** — 认证测试、路径穿越测试、上传限制测试、输入验证测试
6. **清理与完善** — 死代码清除、React ErrorBoundary、可配置 WebSocket URL、API 客户端 delete 方法

## 技术栈

### 后端
- **Python 3.13** + **uv** 包管理器 + **hatchling** 构建系统
- **FastAPI** + uvicorn（异步 Web 框架）
- **SQLAlchemy 2.0** + asyncpg/aiosqlite（异步 ORM + Alembic 迁移）
- **LangChain** + **LangGraph**（AI 编排 + 代理状态机）
- **ChromaDB**（向量存储）+ **FlashRank** / **BGE**（交叉编码器重排序）
- **jieba**（中文分词 ATS 评分）
- **FlagEmbedding**（BGE-M3 多语言嵌入 + BGE 重排序器）
- **ARQ**（异步 Redis 任务队列）
- **Jinja2** + **WeasyPrint**（HTML/PDF 报告生成）
- **Playwright** + **browser-use**（浏览器自动化）
- **FastMCP**（Model Context Protocol 服务器）
- **SlowAPI**（限流）
- **pydantic-settings**（配置管理）

### 前端
- **React 19** + **TypeScript 5.9** + **Vite 7**
- **Zustand 5**（UI状态）+ **TanStack Query v5**（服务端状态+缓存）
- **Recharts 3**（雷达图可视化评分）
- **react-use-websocket**（实时代理更新）
- **Tailwind CSS 4**（样式）
- **React Router v7**（路由）
- **Vitest 4** + **React Testing Library** + **MSW**（测试）

### 基础设施
- **PostgreSQL 16**（主数据库）
- **Redis 7**（任务队列后端）
- **Docker Compose**（6服务部署）
- **Nginx**（生产环境前端反向代理）
- **GitHub Actions**（CI/CD 流水线）

## 许可证

MIT
