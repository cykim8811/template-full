import uuid

from app.core.security import create_access_token
from app.users.models import User


async def test_get_me_no_token(client):
    response = await client.get("/users/me")
    assert response.status_code == 401


async def test_get_me_invalid_token(client):
    response = await client.get(
        "/users/me", headers={"Authorization": "Bearer notavalidtoken"}
    )
    assert response.status_code == 401


async def test_get_me_valid_token_user_not_found(client):
    token = create_access_token(uuid.uuid4())
    response = await client.get(
        "/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


async def test_get_me_returns_current_user(client, db_session):
    user = User(email="me@example.com", username="meuser")
    db_session.add(user)
    await db_session.flush()

    token = create_access_token(user.id)
    response = await client.get(
        "/users/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["username"] == "meuser"
