import os
import sys

# Add parent dir to path so we can import 'app' and 'config'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from app.graph_db.connection import Neo4jConnection
from app.agents.embedding import get_embedding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Fetching a test embedding to determine vector dimension...")
    test_vector = await get_embedding("测试文本")
    dim = len(test_vector)
    logger.info(f"Detected vector dimension: {dim}")
    
    queries = [
        f"CREATE VECTOR INDEX vector_disease_name IF NOT EXISTS FOR (d:Disease) ON (d.embedding) OPTIONS {{indexConfig: {{`vector.dimensions`: {dim}, `vector.similarity_function`: 'cosine'}}}}",
        f"CREATE VECTOR INDEX vector_symptom_name IF NOT EXISTS FOR (s:Symptom) ON (s.embedding) OPTIONS {{indexConfig: {{`vector.dimensions`: {dim}, `vector.similarity_function`: 'cosine'}}}}"
    ]
    
    async with Neo4jConnection.session() as session:
        for q in queries:
            logger.info(f"Executing: {q}")
            await session.run(q)
            
    logger.info("Vector indexes created successfully.")
    await Neo4jConnection.close()

if __name__ == "__main__":
    asyncio.run(main())
