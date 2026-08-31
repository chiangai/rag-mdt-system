class HealthAgent:
    def fallback(self, message: str, context: list[dict]) -> str:
        evidence = f"参考资料提示：{context[0].get('snippet', '')}。" if context else "目前无法取得知识资料。"
        return f"{evidence}我不能替代医生诊断；若症状持续、加重或让你担心，请联系产科医生。"
