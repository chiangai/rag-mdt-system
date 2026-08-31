# HerCare

一个面向求职展示的 C 端产后健康 AI 产品原型。它不宣称真实医疗生产合规，也不诊断或处方；重点展示如何把多 Agent、医学知识图谱、检索、记忆与安全门控落成一个可体验的手机端产品。

## 体验目标

HerCare 的默认入口是 AI 对话，而不是仪表盘。

```text
用户描述感受
→ HerCare 理解意图
→ 健康问题检索受控知识图谱
→ 给出谨慎回答、下一步行动和来源名
→ 将确认后的状态沉淀为时间线 / Care Plan
```

手机端只保留两个一级入口：

- `HerCare AI`：默认首页。快捷问题、对话、输入框和安全提示都在同一屏。
- `我的`：收纳今日状态、恢复记录和 Care Plan，不与 AI 抢入口。

产品只有一个虚构演示商品：**HerCare 7 日恢复营养餐**。它不会出现在主导航中；仅在健康建议存在匹配 Care Action 时由 CommerceAgent 展示。

## 架构

```text
Mobile React UI
  └─ POST /api/v1/chat/stream (SSE)
       └─ FastAPI Simple Harness
            ├─ Input Red-flag Gate
            ├─ MasterAgent: intent / slots / route
            ├─ ChatAgent: 闲聊与陪伴，不调用 RAG
            ├─ HealthAgent: 医学问题，唯一可调用 Hybrid RAG
            ├─ CommerceAgent: 单一演示商品
            ├─ Output Gate / Trace / Memory Policy
            └─ OpenAI-compatible Model Provider
                 └─ DeepSeek V4 Flash / other compatible endpoint

Fixed REST pages
  └─ SQLite (profile, check-in, timeline, care plan, conversation, trace)

Hybrid RAG
  └─ Neo4j: exact/alias + vector Top-K + 1–2 hop expansion
```

固定页面不进入 Agent：`/profile`、`/home`、`/check-ins`、`/timeline`、`/care-plan`、`/product` 都是普通 FastAPI + SQLite 调用。

更完整的职责和数据边界见 [架构说明](docs/architecture.md)。

## 安全边界

- 前端没有、也不能读取模型 API Key。`VITE_TRANSPORT=http` 仅表示前端改走后端 API。
- Key 只放本机根目录 `.env`，并由 FastAPI 读取；`.env` 和 `frontend/.env.local` 都被 Git 忽略。
- 红旗症状在 Agent 前按确定性规则拦截，禁止进入普通健康或商品回答。
- Trace 不包含 Prompt、CoT、原始工具参数或密钥。
- 图谱资产目前仅保留来源名；引用必须标明 `source_name_only`，不伪装成可定位的医学原文证据。

## 技术栈

| 层 | 技术 |
| --- | --- |
| Mobile UI | React 19, TypeScript, Vite, Tailwind |
| API / Agent runtime | FastAPI, Pydantic v2, LangGraph-compatible workflow boundary |
| Data | SQLite + SQLAlchemy 2, Neo4j 5.x |
| Retrieval | 受控 Hybrid RAG（关键词 / 别名、向量、图扩展） |
| Model | OpenAI-compatible adapter，默认支持 DeepSeek |
| Tests | Pytest, Vitest |

## 快速开始

### 1. 后端

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
```

在 `.env` 里填入**仅后端使用**的模型配置：

```dotenv
HERCARE_LLM_API_KEY=your-server-only-key
HERCARE_LLM_BASE_URL=https://api.deepseek.com
HERCARE_LLM_MODEL=deepseek-v4-flash
```

启动：

```powershell
python -m uvicorn app.api.main:app --reload --port 8000
```

### 2. 前端

```powershell
cd frontend
npm install
Set-Content .env.local 'VITE_TRANSPORT=http'
npm run dev
```

浏览器打开 `http://localhost:5173`。Vite 已将 `/api` 代理到 `http://localhost:8000`。

不配置模型 Key 时，后端会使用安全本地 fallback，页面仍可演示，但不会产生真实模型回答。

## 运行状态与路线图

| 能力 | 状态 |
| --- | --- |
| 手机端 AI-first 体验、状态记录、时间线、Care Plan | 已完成 |
| 后端 SSE、幂等、红旗门控、Memory / Trace | 已完成 |
| 后端 OpenAI-compatible Provider、DeepSeek V4 Flash | 已完成 |
| LangGraph StateGraph 实体化编排 | 待接线（当前为同等边界的轻量 workflow） |
| KG 审计、流式 namespaced importer、50-case retrieval eval | 已完成 |
| **真实 Neo4j Hybrid Retriever 注入到运行时** | 待接线 |
| **回答下方展示 RAG citation 卡片** | 待接线 |

因此，当前真实模型回答已可用，但健康回答还不会显示 RAG 引用；这是下一步集成工作，而不是图谱模块缺失。

## 验证

```powershell
python -m pytest tests/backend tests/retrieval -q
cd frontend
npm test
npm run lint
npm run build
```

完整 KG 导入和真实模型 50-case Eval 不在每次提交运行：嵌入资产约 660 MB，只能通过绝对路径 `HERCARE_KG_SOURCE_DIR` 只读访问，不能提交到 Git。

## 目录

```text
app/
  agents/       # Master / Chat / Health / Commerce
  api/          # REST + SSE
  providers/    # server-side OpenAI-compatible adapter
  retrieval/    # Hybrid RAG and Neo4j adapters
  runtime/      # Harness, safety, memory, trace
  storage/      # SQLite model / seed / repository
frontend/       # mobile-first React client
scripts/kg/     # KG audit and namespaced importer
eval/           # versioned 50-case retrieval evaluation
contracts/      # OpenAPI / SSE / domain contracts
docs/           # architecture notes
```
