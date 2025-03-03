from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to AI English Tutor API"}

def test_register():
    response = client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    assert "email" in response.json()

def test_initial_chat():
    # 首先注册并登录
    client.post(
        "/api/auth/register",
        json={
            "email": "chat@example.com",
            "username": "chatuser",
            "password": "chatpass123"
        }
    )
    
    token_response = client.post(
        "/api/auth/token",
        data={
            "username": "chat@example.com",
            "password": "chatpass123"
        }
    )
    
    token = token_response.json()["access_token"]
    
    # 测试初始对话
    response = client.post(
        "/api/assessment/initial-chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "messages": [
                {
                    "role": "user",
                    "content": "你好，我想学习英语"
                }
            ]
        }
    )
    assert response.status_code == 200
    assert "content" in response.json()
