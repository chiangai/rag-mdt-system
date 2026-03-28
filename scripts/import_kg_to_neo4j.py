"""
import_kg_to_neo4j.py
---------------------
将 global_kg_embedded.json 导入 Neo4j，并清空原有数据库。

步骤：
  1. 清空数据库中全部节点和关系
  2. 用 UNWIND 批量写入节点（含 embedding 向量）
  3. 用 UNWIND 批量写入关系（边）
  4. 为 name 属性和 embedding 属性建立索引

节点标签：直接使用 main_category 字段（如 Disease、Symptom 等），
         同时统一打上 :KGNode 标签，方便全量查询。
"""

import os
import sys
import json
import asyncio
import logging
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.graph_db.connection import Neo4jConnection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

ROOT_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE  = os.path.join(ROOT_DIR, "global_kg_embedded.json")
BATCH_SIZE  = 200  # 每批写入节点/关系数量


# ---------- Cypher 模板 ----------

CLEAR_ALL_CYPHER = "MATCH (n) DETACH DELETE n"

# 创建/合并节点：统一打 :KGNode 标签，再额外打 main_category 标签
# 注意：Neo4j 不支持动态标签，需用 apoc 或者预处理。
# 这里改为把 main_category 作为属性存储，同时只打 :KGNode 标签，
# 若你安装了 APOC，可以改为 apoc.create.addLabels 动态添加
MERGE_NODES_CYPHER = """
UNWIND $batch AS item
MERGE (n:KGNode {name: item.name})
SET n.main_category   = item.main_category,
    n.categories      = item.categories,
    n.source_count    = item.source_count,
    n.sources         = item.sources,
    n.embedding       = item.embedding,
    n.embedding_text  = item.embedding_text
"""

MERGE_RELS_CYPHER = """
UNWIND $batch AS item
MATCH (a:KGNode {name: item.source})
MATCH (b:KGNode {name: item.target})
MERGE (a)-[r:RELATED {type: item.type}]->(b)
SET r.weight = item.weight,
    r.docs   = item.docs
"""

CREATE_INDEX_CYPHER = [
    "CREATE INDEX kg_node_name IF NOT EXISTS FOR (n:KGNode) ON (n.name)",
    "CREATE INDEX kg_node_category IF NOT EXISTS FOR (n:KGNode) ON (n.main_category)",
]

# Vector index（Neo4j 5.x，需要先知道向量维度）
VECTOR_INDEX_CYPHER_TEMPLATE = """
CREATE VECTOR INDEX kg_embedding IF NOT EXISTS
FOR (n:KGNode) ON (n.embedding)
OPTIONS {{indexConfig: {{`vector.dimensions`: {dim}, `vector.similarity_function`: 'cosine'}}}}
"""


def chunks(lst: list, n: int):
    """将列表按 n 分批"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


async def clear_database(session):
    logger.info("🗑️  正在清空数据库（DETACH DELETE 全部节点）...")
    # 分批删除，防止大库内存溢出
    while True:
        result = await session.run(
            "MATCH (n) WITH n LIMIT 10000 DETACH DELETE n RETURN count(n) AS deleted"
        )
        records = [r.data() async for r in result]
        deleted = records[0]["deleted"] if records else 0
        logger.info(f"  删除了 {deleted} 个节点")
        if deleted == 0:
            break
    logger.info("✅ 数据库已清空")


async def create_indexes(session, embedding_dim: int):
    for cypher in CREATE_INDEX_CYPHER:
        await session.run(cypher)
        logger.info(f"  索引已创建：{cypher[:60]}")
    if embedding_dim > 0:
        vc = VECTOR_INDEX_CYPHER_TEMPLATE.format(dim=embedding_dim)
        try:
            await session.run(vc)
            logger.info(f"  向量索引已创建（维度={embedding_dim}）")
        except Exception as e:
            logger.warning(f"  向量索引创建失败（可能 Neo4j 版本不支持 5.x 语法）：{e}")
    logger.info("✅ 索引创建完毕")


async def import_nodes(session, nodes: list):
    total = len(nodes)
    count = 0
    start = time.time()

    for batch in chunks(nodes, BATCH_SIZE):
        batch_data = []
        for n in batch:
            batch_data.append({
                "name":           n.get("id", ""),
                "main_category":  n.get("main_category", ""),
                "categories":     n.get("categories", []),
                "source_count":   n.get("source_count", 0),
                "sources":        n.get("sources", []),
                "embedding":      n.get("embedding"),       # list[float] | None
                "embedding_text": n.get("embedding_text", ""),
            })
        await session.run(MERGE_NODES_CYPHER, {"batch": batch_data})
        count += len(batch)
        elapsed = time.time() - start
        logger.info(f"  节点进度：{count}/{total}  ({count/total*100:.1f}%)  耗时 {elapsed:.1f}s")

    logger.info(f"✅ 节点导入完毕，共 {total} 个")


async def import_edges(session, edges: list):
    total = len(edges)
    count = 0
    start = time.time()

    for batch in chunks(edges, BATCH_SIZE):
        batch_data = [
            {
                "source": e["source"],
                "target": e["target"],
                "type":   e.get("type", "RELATED"),
                "weight": e.get("weight", 1),
                "docs":   e.get("docs", []),
            }
            for e in batch
        ]
        try:
            await session.run(MERGE_RELS_CYPHER, {"batch": batch_data})
        except Exception as ex:
            logger.error(f"  批量写入关系失败（跳过）：{ex}")
        count += len(batch)
        elapsed = time.time() - start
        logger.info(f"  关系进度：{count}/{total}  ({count/total*100:.1f}%)  耗时 {elapsed:.1f}s")

    logger.info(f"✅ 关系导入完毕，共 {total} 条")


async def main():
    # 1. 加载文件
    logger.info(f"📂 读取文件：{INPUT_FILE}")
    if not os.path.exists(INPUT_FILE):
        logger.error("找不到文件，请先运行 embed_global_kg.py 生成嵌入向量")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        kg = json.load(f)

    nodes = kg.get("nodes", [])
    edges = kg.get("edges", [])
    logger.info(f"载入 {len(nodes)} 个节点，{len(edges)} 条关系")

    # 推断向量维度
    embedding_dim = 0
    for n in nodes:
        if n.get("embedding"):
            embedding_dim = len(n["embedding"])
            break
    logger.info(f"检测到向量维度：{embedding_dim}")

    # 2. 连接 Neo4j
    ok = await Neo4jConnection.verify_connectivity()
    if not ok:
        logger.error("Neo4j 连接失败，请检查 .env 中的配置")
        return

    async with Neo4jConnection.session() as session:
        # 3. 清空数据库
        await clear_database(session)

        # 4. 建索引（在写入节点前建，提升 MERGE 速度）
        await create_indexes(session, embedding_dim)

        # 5. 导入节点
        logger.info("⬆️  开始导入节点...")
        await import_nodes(session, nodes)

        # 6. 导入关系
        logger.info("🔗 开始导入关系...")
        await import_edges(session, edges)

    await Neo4jConnection.close()
    logger.info("🎉 全部完成！")


if __name__ == "__main__":
    asyncio.run(main())
