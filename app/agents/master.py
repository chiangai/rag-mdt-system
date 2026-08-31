from __future__ import annotations


class MasterAgent:
    HEALTH_TERMS = ("孕", "头痛", "疼", "出血", "血压", "药", "症状", "医生", "health", "pain")
    COMMERCE_TERMS = ("买", "商品", "产品", "推荐枕", "价格", "product", "buy")

    def route(self, message: str) -> str:
        normalized = message.casefold()
        if any(term in normalized for term in self.COMMERCE_TERMS):
            return "commerce"
        if any(term in normalized for term in self.HEALTH_TERMS):
            return "health"
        return "chat"
