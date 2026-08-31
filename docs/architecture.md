# HerCare 架构说明

## 第一原则

固定页面要确定、便宜、可审计；只有“用户想表达什么、需要怎样的解释”才需要 Agent。因此页面功能和 AI 对话是两条调用链。

```text
固定页面
→ FastAPI service
→ SQLite
→ 不调用 Agent

Ask HerCare
→ FastAPI SSE
→ Harness
→ MasterAgent
→ ChatAgent | HealthAgent | CommerceAgent
```

当前 `HerCareWorkflow` 已按上述边界编排，但仍是轻量实现；`langgraph` 依赖已保留，后续可将该 workflow 实体化为 `StateGraph`，不改变 API 或 Agent 职责。

## Agent 边界

| 组件 | 只负责 | 明确不负责 |
| --- | --- | --- |
| MasterAgent | 意图、槽位、路由、至多 3 项任务计划 | 医学回答、RAG、商品事实、持久化 |
| ChatAgent | 闲聊、低风险陪伴、功能引导 | 医学工具、诊断、商品适配判断 |
| HealthAgent | 症状咨询、恢复解释、Care Plan | 自由 Cypher、商品操作、处方 |
| CommerceAgent | 一个营养餐演示商品的信息与适配说明 | 商品比较、支付、订单、医学 RAG |
| Harness | 红旗、输出门控、Memory、Trace、重试、超时 | 替 Agent 进行业务推理 |

## Health RAG

HealthAgent 是唯一可触发医学检索的业务 Agent。

```text
health query
→ exact / alias search
+ vector Top-K
→ 1–2 hop graph expansion
→ dedupe / fusion
→ EvidenceItem
→ grounded answer + citation
```

Agent 不获得 Cypher 工具。Neo4j 适配器只接受固定、带 `dataset_id` 的查询模板。所有 EvidenceItem 都包含：`kg_node_id`、图路径、检索分数、数据版本和来源名。

> 当前图谱没有原文证据片段，故 citation 质量固定为 `source_name_only`。页面必须显示“知识图谱来源名，原文未收录”。

## 运行时状态

| 状态 | 存放位置 | 用途 |
| --- | --- | --- |
| 用户、Check-in、Health Event、Care Plan | SQLite | 事实源 |
| 会话短记忆、确认后的候选记忆 | SQLite | 下一轮压缩上下文 |
| Trace | SQLite | 审计，不进入下一轮提示词 |
| 医学实体、关系、embedding | Neo4j | 受控检索 |

Health Event 是追加写入；模型推断不能覆盖旧症状或直接升级成事实。Agent 只能提出 `memory_candidates`，最终写入由 Harness policy 决定。

## 安全与降级

1. 输入先过红旗规则。命中时立即返回线下就医提示，阻止 Health / Commerce 路径。
2. 检索不可用时 Health 回答必须标记 degraded，不能伪造引用。
3. 模型不可用时返回本地安全 fallback。
4. SSE 只允许：`message.start`、`message.delta`、`safety.escalation`、`message.completed`、`error`。
5. 前端不接收 Prompt、CoT、密钥、原始 Cypher 或内部工具参数。

## 当前集成缺口

数据模块已经实现 KG audit、导入器、`HybridRetriever` 与测试 fixture；但 API 启动时尚未构造 Neo4j driver、query embedding adapter 并将 retriever 注入 Harness。因此真实模型已经能回答，真实 RAG citation 尚未进入该运行时链路。
