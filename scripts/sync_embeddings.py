import os
import sys

# Add parent dir to path so we can import 'app' and 'config'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from app.graph_db.connection import Neo4jConnection
from app.agents.embedding import get_embedding
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info(f"Initializing Volcengine Embeddings with model: {settings.llm.ark_embedding_model}")
    
    async with Neo4jConnection.session() as session:
        # 1. Process Disease nodes
        result = await session.run("MATCH (d:Disease) WHERE d.embedding IS NULL RETURN elementId(d) AS id, d.name AS name")
        nodes = [record.data() async for record in result]
        
        logger.info(f"Found {len(nodes)} Disease nodes without embeddings.")
        
        for idx, node in enumerate(nodes):
            vector = await get_embedding(node["name"])
            await session.run(
                "MATCH (d:Disease) WHERE elementId(d) = $id SET d.embedding = $vector", 
                {"id": node["id"], "vector": vector}
            )
            logger.info(f"[{idx+1}/{len(nodes)}] Updated embedding for Disease: {node['name']}")
            
        # 2. Process Symptom nodes
        result = await session.run("MATCH (s:Symptom) WHERE s.embedding IS NULL RETURN elementId(s) AS id, s.name AS name")
        nodes = [record.data() async for record in result]
        
        logger.info(f"Found {len(nodes)} Symptom nodes without embeddings.")
        
        for idx, node in enumerate(nodes):
            vector = await get_embedding(node["name"])
            await session.run(
                "MATCH (s:Symptom) WHERE elementId(s) = $id SET s.embedding = $vector", 
                {"id": node["id"], "vector": vector}
            )
            logger.info(f"[{idx+1}/{len(nodes)}] Updated embedding for Symptom: {node['name']}")
            
    logger.info("Embeddings sync completed.")
    await Neo4jConnection.close()

if __name__ == "__main__":
    asyncio.run(main())
