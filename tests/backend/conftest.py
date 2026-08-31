from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    database_url = f"sqlite:///{(tmp_path / 'hercare-test.db').as_posix()}"
    app = create_app(database_url=database_url)
    with TestClient(app) as test_client:
        yield test_client
