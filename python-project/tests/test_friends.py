from types import SimpleNamespace
from uuid import uuid4

from app.depends import get_current_user, get_friend_service
from app.schemas import FriendRequestListItem, FriendRead, FriendStatusRead


def _user(name: str, friend_tag: str, avatar_url: str | None = None):
    return SimpleNamespace(
        id=uuid4(),
        name=name,
        avatar_url=avatar_url,
        friend_tag=friend_tag,
    )


class FakeFriendService:
    def __init__(self, requester, target):
        self.requester = requester
        self.target = target
        self._request_id = uuid4()

    def send_request(self, requester_id, target_tag):
        return FriendRequestListItem(
            request_id=self._request_id,
            user=FriendRead(
                id=self.target.id,
                friend_tag=self.target.friend_tag,
                name=self.target.name,
                avatar_url=self.target.avatar_url,
                anonymous_number="0001",
            ),
        )

    def list_outgoing(self, user_id):
        return [self.send_request(user_id, self.target.friend_tag)]

    def list_incoming(self, user_id):
        return [
            FriendRequestListItem(
                request_id=self._request_id,
                user=FriendRead(
                    id=self.requester.id,
                    friend_tag=self.requester.friend_tag,
                    name=self.requester.name,
                    avatar_url=self.requester.avatar_url,
                    anonymous_number="0001",
                ),
            )
        ]

    def accept_request(self, addressee_id, request_id):
        return FriendRead(
            id=self.requester.id,
            friend_tag=self.requester.friend_tag,
            name=self.requester.name,
            avatar_url=self.requester.avatar_url,
            anonymous_number="0001",
        )

    def decline_request(self, addressee_id, request_id):
        return None

    def cancel_request(self, requester_id, request_id):
        return None

    def get_friend_user(self, current_user_id, target_user_id):
        if target_user_id != self.target.id:
            from app.errors import raise_http
            raise_http(404, "USER_NOT_FOUND", "User not found")
        return FriendStatusRead(
            is_friend=False,
            user=FriendRead(
                id=self.target.id,
                friend_tag=self.target.friend_tag,
                name=self.target.name,
                avatar_url=self.target.avatar_url,
                anonymous_number="0001",
            ),
        )


def test_send_request_and_lists(client):
    requester = _user("Requester", "REQ-TAG")
    target = _user("Target", "TAR-TAG", "http://img")

    client.app.dependency_overrides[get_current_user] = lambda: requester
    client.app.dependency_overrides[get_friend_service] = lambda: FakeFriendService(requester, target)

    response = client.post("/friends/requests", json={"friend_tag": target.friend_tag})
    assert response.status_code == 200
    payload = response.json()
    assert "requestId" in payload
    assert payload["user"]["id"] == str(target.id)
    assert payload["user"]["name"] == "Target"
    assert payload["user"]["avatar_url"] == "http://img"
    assert payload["user"]["friend_tag"] == "TAR-TAG"
    assert payload["user"]["anonymous_number"] == "0001"

    outgoing = client.get("/friends/requests/outgoing")
    assert outgoing.status_code == 200
    outgoing_payload = outgoing.json()
    assert len(outgoing_payload) == 1
    assert outgoing_payload[0]["requestId"] == payload["requestId"]

    incoming = client.get("/friends/requests/incoming")
    assert incoming.status_code == 200
    incoming_payload = incoming.json()
    assert len(incoming_payload) == 1
    assert incoming_payload[0]["user"]["id"] == str(requester.id)
    assert incoming_payload[0]["user"]["name"] is not None


def test_accept_request_returns_friend(client):
    requester = _user("Requester", "REQ-TAG")
    addressee = _user("Addressee", "ADD-TAG")
    service = FakeFriendService(requester, addressee)

    client.app.dependency_overrides[get_current_user] = lambda: addressee
    client.app.dependency_overrides[get_friend_service] = lambda: service

    accept = client.post("/friends/requests/accept", json={"requestId": str(service._request_id)})
    assert accept.status_code == 200
    payload = accept.json()
    assert payload["id"] == str(requester.id)
    assert payload["friend_tag"] == requester.friend_tag


def test_get_friend_user_returns_is_friend_and_user(client):
    requester = _user("Requester", "REQ-TAG")
    target = _user("Target", "TAR-TAG", "http://img")

    client.app.dependency_overrides[get_current_user] = lambda: requester
    client.app.dependency_overrides[get_friend_service] = lambda: FakeFriendService(requester, target)

    response = client.get(f"/friends/{target.id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["is_friend"] is False
    assert payload["user"]["id"] == str(target.id)
    assert payload["user"]["friend_tag"] == "TAR-TAG"
    assert payload["user"]["name"] == "Target"
    assert payload["user"]["avatar_url"] == "http://img"
    assert payload["user"]["anonymous_number"] == "0001"
