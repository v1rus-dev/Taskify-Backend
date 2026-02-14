import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("AUTO_CREATE_TABLES", "false")

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
