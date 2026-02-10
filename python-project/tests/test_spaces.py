from types import SimpleNamespace
from uuid import uuid4

from app.depends import (
    get_current_user,
    get_space_interactor,
    get_space_task_interactor,
)


def _user():
    return SimpleNamespace(id=uuid4())


class FakeSpaceInteractor:
    def __init__(self):
        self.space_id = 101

    def create_space(self, user_id, name, description, is_lightweight=False):
        return {
            "id": self.space_id,
            "name": name,
            "description": description,
            "is_lightweight": is_lightweight,
            "created_by": str(user_id),
            "created_at": "2026-02-09T10:00:00Z",
            "updated_at": "2026-02-09T10:00:00Z",
        }

    def list_spaces(self, user_id):
        return [self.create_space(user_id, "Team", None)]

    def get_space(self, user_id, space_id):
        return self.create_space(user_id, "Team", None)


class FakeTaskInteractor:
    def complete(self, user_id, space_id, task_id, is_completed):
        return {
            "id": task_id,
            "space_id": space_id,
            "list_id": None,
            "title": "Task",
            "description": None,
            "assignee_id": str(user_id),
            "claimed_by_id": None,
            "completed_at": "2026-02-09T10:00:00Z" if is_completed else None,
            "deleted_at": None,
            "created_by": str(user_id),
            "updated_by": str(user_id),
            "created_at": "2026-02-09T10:00:00Z",
            "updated_at": "2026-02-09T10:00:00Z",
        }


def test_create_space(client):
    current_user = _user()
    client.app.dependency_overrides[get_current_user] = lambda: current_user
    client.app.dependency_overrides[get_space_interactor] = lambda: FakeSpaceInteractor()

    response = client.post("/spaces", json={"name": "Team", "description": "MVP", "is_lightweight": False})

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Team"
    assert payload["description"] == "MVP"


def test_complete_task_endpoint(client):
    current_user = _user()
    client.app.dependency_overrides[get_current_user] = lambda: current_user
    client.app.dependency_overrides[get_space_task_interactor] = lambda: FakeTaskInteractor()

    response = client.post(
        "/spaces/101/tasks/55/complete",
        json={"is_completed": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 55
    assert payload["completed_at"] is not None
