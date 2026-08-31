from __future__ import annotations


RED_FLAGS = ("大量出血", "快晕倒", "晕厥", "胸痛", "呼吸困难", "severe bleeding", "fainting", "chest pain", "difficulty breathing")


def detect_red_flags(message: str) -> list[str]:
    normalized = message.casefold()
    return [flag for flag in RED_FLAGS if flag in normalized]


def urgent_guidance() -> str:
    return "这可能是需要立即处理的危险信号。请立即联系当地急救服务或前往急诊，并请身边的人陪同；不要等待在线回复。"
