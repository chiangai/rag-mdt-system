# 妇产科 AI 虚拟 MDT 多智能体会诊系统

基于 Neo4j 知识图谱 + LangGraph 多智能体编排 + FastAPI + React，实现妇产科多学科会诊 (MDT) 的 AI 辅助系统。

## 架构

系统由 5 个智能体协同工作：

1. **导诊/规划智能体** — 接收患者主诉，提取医学实体，规划需要介入的科室
2. **图谱查询智能体** — 将医学实体转化为 Cypher 查询，从知识图谱中检索循证知识
3. **产科专家智能体** — 从产科角度评估孕妇和胎儿风险，给出诊疗建议
4. **内分泌专家智能体** — 从代谢角度评估风险，给出控糖/控压等建议
5. **医疗审查/安全智能体** — 交叉比对各专家建议和药物禁忌，确保输出安全

## 快速开始

### 后端

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key 和 Neo4j 连接信息

# 3. 导入示例知识图谱数据到 Neo4j
# 将 data/sample_graph.cypher 内容在 Neo4j Browser 中执行

# 4. 启动后端
uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:3000
```

前端开发模式自动代理 `/api` 请求到后端 `localhost:8000`，无需额外 CORS 配置。

## API

- `POST /api/v1/consult` — 同步会诊
- `POST /api/v1/consult/stream` — SSE 流式会诊（前端实时展示进度）
- `GET /api/v1/consult/{id}` — 查询历史会诊
- `GET /api/v1/consult/{id}/trace` — 查看推理过程
- `GET /health` — 健康检查

## 核心特色：语义向量搜索 (Vector Search)

系统集成了 **Neo4j 向量检索**，配合火山引擎 (Volcengine) 的多模态 Embedding 模型，极大提升了医学实体的召回率：
- **语义匹配**：能够识别“口渴”与“多饮”、“大肚子”与“妊娠”之间的语义关联。
- **自动降级**：当传统 Cypher 模板匹配失败时，智能体自动切换为向量检索。
- **高性能**：在本地 Neo4j 中建立向量索引，支持毫秒级 KNN 检索。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React + Vite + TailwindCSS |
| 后端 | FastAPI + Uvicorn |
| 智能体编排 | LangGraph (async) |
| LLM 抽象层 | LangChain |
| 知识图谱 | Neo4j + Vector Index |
| 推荐 LLM | DeepSeek-V3 (deepseek-chat) |
| 向量模型 | Volcengine Multimodal Embedding |

## 快速开发与同步

```bash
# 向量化图谱数据
python scripts/setup_vector_index.py
python scripts/sync_embeddings.py
```
