"""
embed_global_kg.py
------------------
读取项目根目录下的 global_kg.json，对每个节点的「名称 + 分类」
进行向量嵌入，并将结果写出到 global_kg_embedded.json。

说明：
- 嵌入文本格式：「分类：{main_category}，名称：{id}」
- 调用 app.agents.embedding.get_embedding（火山引擎 ARK API）
- 支持断点续传：若已存在 global_kg_embedded.json，则跳过已处理节点
- 每处理 SAVE_INTERVAL 个节点自动保存一次进度
"""

import os
import sys
import json
import asyncio
import logging
import time

# 确保可以 import app/config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.embedding import get_embedding

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

ROOT_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE     = os.path.join(ROOT_DIR, "global_kg.json")
OUTPUT_FILE    = os.path.join(ROOT_DIR, "global_kg_embedded.json")
SAVE_INTERVAL  = 100   # 每处理 N 个节点保存一次
CONCURRENCY    = 5     # 并发请求数（太高容易触发速率限制）
RETRY_TIMES    = 3     # 失败重试次数
RETRY_DELAY    = 2.0   # 重试等待秒数


def build_text(node: dict) -> str:
    """拼接用于 embedding 的文本：「分类：XX，名称：XX」"""
    category = node.get("main_category", "未知")
    name     = node.get("id", "")
    return f"分类：{category}，名称：{name}"


async def embed_with_retry(text: str) -> list[float] | None:
    """带重试的 embedding 调用"""
    for attempt in range(1, RETRY_TIMES + 1):
        try:
            return await get_embedding(text)
        except Exception as e:
            logger.warning(f"第 {attempt}/{RETRY_TIMES} 次尝试失败：{e}")
            if attempt < RETRY_TIMES:
                await asyncio.sleep(RETRY_DELAY * attempt)
    logger.error(f"放弃对文本的 embedding：{text!r}")
    return None


async def main():
    # 加载原始知识图谱
    logger.info(f"读取知识图谱：{INPUT_FILE}")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        kg = json.load(f)

    nodes = kg.get("nodes", [])
    total = len(nodes)
    logger.info(f"共 {total} 个节点，{len(kg.get('edges', []))} 条边")

    # 断点续传：读取已有输出文件
    done_ids: set[str] = set()
    if os.path.exists(OUTPUT_FILE):
        logger.info(f"发现已有输出文件，加载进度：{OUTPUT_FILE}")
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
        # 以 embedded 节点的 id 做去重集合
        for n in existing.get("nodes", []):
            if "embedding" in n and n["embedding"] is not None:
                done_ids.add(n["id"])
        logger.info(f"已完成 {len(done_ids)} 个节点，继续处理剩余节点")
        # 将已有节点合并到工作列表
        existing_map = {n["id"]: n for n in existing.get("nodes", [])}
    else:
        existing_map = {}

    # 构建待处理列表
    pending = [n for n in nodes if n["id"] not in done_ids]
    logger.info(f"待处理：{len(pending)} 个节点")

    # 合并已有节点（含 embedding）和原始节点（尚未处理）
    result_nodes = list(existing_map.values())
    for n in nodes:
        if n["id"] not in existing_map:
            result_nodes_ids = {rn["id"] for rn in result_nodes}
            if n["id"] not in result_nodes_ids:
                result_nodes.append(dict(n))  # 先不含 embedding

    # 建立 id -> result_nodes 的索引方便回写
    result_map = {n["id"]: n for n in result_nodes}

    # 并发信号量
    sem = asyncio.Semaphore(CONCURRENCY)
    processed_count = 0
    start_time = time.time()

    async def process_one(node: dict):
        nonlocal processed_count
        text = build_text(node)
        async with sem:
            vec = await embed_with_retry(text)
        result_map[node["id"]]["embedding"] = vec
        result_map[node["id"]]["embedding_text"] = text
        processed_count += 1

        # 定期保存
        if processed_count % SAVE_INTERVAL == 0:
            elapsed = time.time() - start_time
            speed = processed_count / elapsed
            remaining = (len(pending) - processed_count) / speed if speed > 0 else 0
            logger.info(
                f"进度 {processed_count}/{len(pending)} "
                f"({processed_count/len(pending)*100:.1f}%)  "
                f"速度 {speed:.1f} 个/秒  "
                f"预计剩余 {remaining/60:.1f} 分钟"
            )
            _save(kg, result_map)

    # 并发执行
    tasks = [process_one(n) for n in pending]
    await asyncio.gather(*tasks)

    # 最终保存
    _save(kg, result_map)
    elapsed = time.time() - start_time
    logger.info(f"全部完成！共处理 {processed_count} 个节点，耗时 {elapsed:.1f}s")
    logger.info(f"结果已保存至：{OUTPUT_FILE}")


def _save(original_kg: dict, result_map: dict):
    """将结果写出到 OUTPUT_FILE"""
    output = {
        "metadata": original_kg.get("metadata", {}),
        "nodes": list(result_map.values()),
        "edges": original_kg.get("edges", [])
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    logger.info(f"已保存进度到 {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
