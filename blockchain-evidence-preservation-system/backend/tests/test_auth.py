"""
Tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, sample_user_data: dict):
    response = await client.post("/api/v1/auth/register", json=sample_user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == sample_user_data["email"]
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, sample_user_data: dict):
    await client.post("/api/v1/auth/register", json=sample_user_data)
    response = await client.post("/api/v1/auth/register", json=sample_user_data)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, sample_user_data: dict):
    await client.post("/api/v1/auth/register", json=sample_user_data)
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": sample_user_data["email"],
            "password": sample_user_data["password"],
        },
    )
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, sample_user_data: dict):
    await client.post("/api/v1/auth/register", json=sample_user_data)
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": sample_user_data["email"], "password": "WrongPassword!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, sample_user_data: dict):
    await client.post("/api/v1/auth/register", json=sample_user_data)
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={
            "username": sample_user_data["email"],
            "password": sample_user_data["password"],
        },
    )
    token = login_resp.json()["access_token"]
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == sample_user_data["email"]


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
