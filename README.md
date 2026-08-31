# HerCare

HerCare 是一个可完整演示的 C 端产后健康 AI 产品原型，面向求职展示，不宣称真实医疗生产合规。

## 调用边界

固定页面（Home、Check-in、Timeline、Care Plan、Product）走普通 FastAPI REST，不调用 Agent。只有 Ask HerCare 进入 Harness → LangGraph：MasterAgent 负责路由，ChatAgent 负责闲聊，HealthAgent 独占医学 Hybrid RAG，CommerceAgent 只查询一个演示营养餐商品。Memory、Safety、Trace、Retry 都由 Harness 负责。

## 本地启动

```powershell
pip install -r requirements.txt
uvicorn app.api.main:app --reload
cd frontend; npm install; npm run dev
```

默认前端使用 Mock Transport；设置 `VITE_TRANSPORT=http` 后连接 API。KG 资产通过绝对路径 `HERCARE_KG_SOURCE_DIR` 只读挂载；不要将 660MB embedded JSON 提交到 Git。

## 验证

```powershell
python -m pytest tests/backend tests/retrieval -q
cd frontend; npm test; npm run lint; npm run build
docker compose up --build
```

引用仅展示现有知识图谱来源名，并明确标记 `source_name_only`（未收录原文定位）。
