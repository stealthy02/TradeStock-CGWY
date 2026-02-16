# 测试示例文件
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """测试根路径接口"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "docs" in response.json()


def test_read_root():
    """测试首页接口"""
    response = client.get("/api/home/dashboard")
    assert response.status_code == 200
    assert "code" in response.json()
    assert response.json()["code"] == 200
