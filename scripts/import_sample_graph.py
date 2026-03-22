import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from app.graph_db.connection import Neo4jConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sample_graph.cypher')
    
    if not os.path.exists(file_path):
        logger.error(f"Cannot find {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by semicolon to get individual commands
    commands = [cmd.strip() for cmd in content.split(';') if cmd.strip()]

    async with Neo4jConnection.session() as session:
        for i, cmd in enumerate(commands):
            if cmd.startswith('//'):
                continue
            logger.info(f"Executing command {i+1}/{len(commands)}...")
            try:
                await session.run(cmd)
            except Exception as e:
                logger.error(f"Error executing command: {e}\nCommand was: {cmd[:100]}...")

    logger.info("Successfully imported all graph data!")
    await Neo4jConnection.close()

if __name__ == "__main__":
    asyncio.run(main())
