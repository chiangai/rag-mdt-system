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
    session.add(Profile(id="profile-demo", name="小禾", pregnancy_week=24, due_date="2026-12-18", concerns=["睡眠", "营养", "产检提醒"]))
    session.add_all([
        TimelineEvent(id="timeline-welcome", kind="milestone", title="进入孕中期", detail="保持规律产检，并记录身体变化。", occurred_at=utcnow()),
        CarePlanItem(id="care-prenatal", title="预约常规产检", description="按医生建议完成孕中期检查。", cadence="本周"),
        CarePlanItem(id="care-movement", title="记录胎动", description="从固定时段开始熟悉宝宝的活动规律。", cadence="每日"),
        Product(id="product-pillow", name="侧睡支撑枕", category="睡眠支持", summary="帮助侧睡时支撑腰腹，选择透气且便于清洗的材质。", disclaimer="商品信息仅用于生活方式参考，不构成医疗建议或疗效承诺。"),
    ])
    session.commit()
