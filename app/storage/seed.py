from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.storage.models import CarePlanItem, Product, Profile, TimelineEvent


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def seed_demo(session: Session) -> None:
    if session.scalar(select(func.count(Profile.id))):
        return
    session.add(Profile(id="profile-demo", name="小禾", pregnancy_week=8, due_date="2026-07-06", concerns=["睡眠", "营养", "恢复"]))
    session.add_all([
        TimelineEvent(id="timeline-welcome", kind="milestone", title="产后第 8 周恢复记录", detail="继续记录睡眠、情绪和身体变化。", occurred_at=utcnow()),
        CarePlanItem(id="care-rest", title="安排一段连续休息", description="与家人协作，优先保证恢复所需的休息。", cadence="每日"),
        CarePlanItem(id="care-checkin", title="完成今日状态记录", description="记录疼痛、出血、情绪和睡眠变化。", cadence="每日"),
        Product(id="product-meal-7d", name="HerCare 7日恢复营养餐", category="产后营养", summary="虚构的 7 日配送套餐，提供方便准备的均衡餐食。", disclaimer="商品信息仅用于生活方式参考，不构成医疗建议或疗效承诺。"),
    ])
    session.commit()
