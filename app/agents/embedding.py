import httpx
import logging
import json
from config.settings import settings

logger = logging.getLogger(__name__)


def _resolve_tls_verify() -> bool | str:
    if settings.llm.ark_ca_bundle:
        return settings.llm.ark_ca_bundle
    if not settings.llm.ark_ssl_verify:
        logger.warning("ARK SSL verification is disabled. This is unsafe in production.")
    return settings.llm.ark_ssl_verify


async def get_embedding(text: str) -> list[float]:
    """Get embedding vector for the given text using the configured Volcengine model."""
    url = "https://ark.cn-beijing.volces.com/api/v3/embeddings/multimodal"
    api_key = settings.llm.ark_api_key
    model = settings.llm.ark_embedding_model

    if not api_key:
        raise ValueError("ARK_API_KEY is not configured in environment variables.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model,
        "input": [
            {
                "type": "text",
                "text": text
            }
        ]
    }
    
    verify = _resolve_tls_verify()
    async with httpx.AsyncClient(verify=verify) as client:
        response = await client.post(url, headers=headers, json=data, timeout=30.0)
        response.raise_for_status()
        res_json = response.json()
        
        # We need to gracefully handle different Volcengine response structures.
        try:
            if 'data' in res_json:
                data_field = res_json['data']
                if isinstance(data_field, list):
                    # Standard OpenAI format: "data": [{"embedding": [...]}]
                    return data_field[0]['embedding']
                elif isinstance(data_field, dict):
                    # Some custom formats return "data": {"embedding": [...]}
                    if 'embedding' in data_field:
                        return data_field['embedding']
                    elif 'embeddings' in data_field:
                        return data_field['embeddings']
            
            # If we fall through, dump the JSON so the user can show it to us
            logger.error("Could not find embedding in response. Full JSON: %s", json.dumps(res_json, ensure_ascii=False))
            raise ValueError(f"Unrecognized embedding response format: {res_json}")
            
        except Exception as e:
            logger.error("Failed to parse embedding response. Full JSON: %s", json.dumps(res_json, ensure_ascii=False))
            raise e
