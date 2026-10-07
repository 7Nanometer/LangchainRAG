# -*- coding: utf-8 -*-
"""
冒烟测试：不依赖 AI 模型和网络，快速验证核心链路没坏

跑法（在 backend 目录）：
    venv 的 python -m pytest tests/test_smoke.py -v
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """
    整个测试模块共用一个测试客户端。
    注意：必须用 with 语句进入上下文，服务的"启动事件"才会执行
    （建数据库表、自动创建管理员）——普通构造 TestClient(app) 不会触发。
    """
    with TestClient(app) as c:
        yield c


def test_health(client):
    """服务健康检查"""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_admin_account_created(client):
    """管理员账号已自动创建，且角色正确（账号密码从 .env 读取，不硬编码）"""
    from app.config import settings

    if not settings.admin_password:
        pytest.skip("未配置管理员密码（backend/.env 缺失），跳过本项")
    resp = client.post(
        "/api/auth/login",
        json={"username": settings.admin_username, "password": settings.admin_password},
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["role"] == "admin"


def test_register_login_change_password(client):
    """完整走一遍：注册 → 登录 → 查我 → 改密 → 旧密码失效 → 新密码可登录"""
    name = "t" + uuid.uuid4().hex[:8]

    # 注册
    resp = client.post("/api/auth/register", json={"username": name, "password": "abc12345"})
    assert resp.status_code == 200, resp.text

    # 重复注册被拒
    resp = client.post("/api/auth/register", json={"username": name, "password": "abc12345"})
    assert resp.status_code == 400
    assert "已被占用" in resp.json()["message"]

    # 弱密码被拒（纯数字）
    resp = client.post(
        "/api/auth/register", json={"username": name + "x", "password": "12345678"}
    )
    assert resp.status_code == 422

    # 登录
    resp = client.post("/api/auth/login", json={"username": name, "password": "abc12345"})
    assert resp.status_code == 200
    token = resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 查我
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == name
    assert resp.json()["role"] == "user"

    # 改密（旧密码错 → 400）
    resp = client.post(
        "/api/auth/change-password",
        json={"old_password": "wrong-pass1", "new_password": "xyz98765"},
        headers=headers,
    )
    assert resp.status_code == 400

    # 改密（正确）
    resp = client.post(
        "/api/auth/change-password",
        json={"old_password": "abc12345", "new_password": "xyz98765"},
        headers=headers,
    )
    assert resp.status_code == 200

    # 旧密码登录失败
    resp = client.post("/api/auth/login", json={"username": name, "password": "abc12345"})
    assert resp.status_code == 401

    # 新密码登录成功
    resp = client.post("/api/auth/login", json={"username": name, "password": "xyz98765"})
    assert resp.status_code == 200


def test_no_token_rejected(client):
    """没带通行证访问受保护接口 → 401"""
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_wrong_password_rejected(client):
    """密码错误 → 401，且提示不泄露"用户是否存在" """
    resp = client.post("/api/auth/login", json={"username": "7Nanometer", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["message"] == "用户名或密码错误"
