from app.storage.repository import HerCareRepository


class ConversationMemory:
    def load(self, repository: HerCareRepository, conversation_id: str) -> list[dict]:
        return repository.memory(conversation_id)
