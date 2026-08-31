from __future__ import annotations

from fastapi.testclient import TestClient


def test_seeded_fixed_pages_are_available_without_running_agents(client: TestClient) -> None:
    class ForbiddenHarness:
        def run(self, *args, **kwargs):
            raise AssertionError("fixed pages must never invoke the agent harness")

    client.app.state.harness = ForbiddenHarness()

    profile = client.get("/api/v1/profile")
    home = client.get("/api/v1/home")
    timeline = client.get("/api/v1/timeline")
    care_plan = client.get("/api/v1/care-plan")
    product = client.get("/api/v1/product")

    assert profile.status_code == 200
    assert profile.json()["name"] == "小禾"
    assert home.status_code == 200
    assert home.json()["profile"]["postpartum_week"] == 8
    assert timeline.status_code == 200
    assert timeline.json()["items"]
    assert care_plan.status_code == 200
    assert care_plan.json()["items"]
    assert product.status_code == 200
    assert product.json()["items"][0]["disclaimer"]


def test_check_in_idempotency_prevents_duplicate_timeline_entries(
    client: TestClient,
) -> None:
    payload = {
        "metric_type": "mood",
        "value": "calm",
        "note": "slept well",
    }
    headers = {"Idempotency-Key": "checkin-2026-08-31"}

    first = client.post("/api/v1/check-ins", json=payload, headers=headers)
    second = client.post("/api/v1/check-ins", json=payload, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json() == first.json()
    timeline = client.get("/api/v1/timeline").json()["items"]
    matching = [item for item in timeline if item.get("check_in_id") == first.json()["id"]]
    assert len(matching) == 1


def test_care_plan_item_can_be_completed_idempotently(client: TestClient) -> None:
    item = client.get("/api/v1/care-plan").json()["items"][0]

    first = client.patch(
        f"/api/v1/care-plan/items/{item['id']}", json={"completed": True}
    )
    second = client.patch(
        f"/api/v1/care-plan/items/{item['id']}", json={"completed": True}
    )

    assert first.status_code == 200
    assert first.json()["completed"] is True
    assert second.status_code == 200
    assert second.json()["completed_at"] == first.json()["completed_at"]


def test_unknown_care_plan_item_returns_404(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/care-plan/items/missing", json={"completed": True}
    )

    assert response.status_code == 404
