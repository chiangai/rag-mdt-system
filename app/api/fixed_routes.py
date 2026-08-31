from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status

from app.api.schemas import CarePlanUpdate, CheckInRequest
from app.storage.repository import HerCareRepository


def build_fixed_router(repository: Callable[[], HerCareRepository]) -> APIRouter:
    router = APIRouter(prefix="/api/v1")

    @router.get("/profile")
    def get_profile(repo: HerCareRepository = Depends(repository)) -> dict:
        return repo.profile()

    @router.get("/home")
    def get_home(repo: HerCareRepository = Depends(repository)) -> dict:
        care_plan, timeline = repo.care_plan(), repo.timeline()
        return {"profile": repo.profile(), "care_plan_progress": {"completed": sum(item["completed"] for item in care_plan), "total": len(care_plan)}, "latest_timeline_item": timeline[0] if timeline else None, "quick_actions": ["记录感受", "查看计划", "问问 HerCare"]}

    @router.post("/check-ins", status_code=status.HTTP_201_CREATED)
    def create_check_in(payload: CheckInRequest, response: Response, idempotency_key: str = Header(min_length=1, max_length=128), repo: HerCareRepository = Depends(repository)) -> dict:
        result, created = repo.create_check_in(idempotency_key=idempotency_key, data=payload.model_dump())
        response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return result

    @router.get("/timeline")
    def get_timeline(repo: HerCareRepository = Depends(repository)) -> dict:
        return {"items": repo.timeline()}

    @router.get("/care-plan")
    def get_care_plan(repo: HerCareRepository = Depends(repository)) -> dict:
        return {"items": repo.care_plan()}

    @router.patch("/care-plan/items/{item_id}")
    def update_care_plan(item_id: str, payload: CarePlanUpdate, repo: HerCareRepository = Depends(repository)) -> dict:
        try:
            return repo.update_care_plan(item_id, payload.completed)
        except LookupError as error:
            raise HTTPException(status_code=404, detail="care plan item not found") from error

    @router.get("/product")
    def get_product(repo: HerCareRepository = Depends(repository)) -> dict:
        return {"items": repo.products()}

    return router
