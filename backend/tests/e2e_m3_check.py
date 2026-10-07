# -*- coding: utf-8 -*-
"""
M3 端到端检查：问答链路全流程验证
（SSE 流式事件 → 落库 → 会话管理 → 反馈 → 导出 → 权限）

跑法（服务启动后）：
    RAG_BASE_URL=http://127.0.0.1:8001 python tests/e2e_m3_check.py
配合以 RAG_FAKE_LLM=1 启动的服务，可离线验证全链路（不调用真实 API、不花钱）。
"""
import json
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import httpx  # noqa: E402

from app.config import settings  # noqa: E402

BASE = os.environ.get("RAG_BASE_URL") or "http://127.0.0.1:8000"


def parse_sse(lines) -> list[dict]:
    """把 SSE 行流解析成 [{event, data}, ...]"""
    events: list[dict] = []
    current: dict = {}
    for line in lines:
        if line.startswith("event: "):
            current["event"] = line[7:]
        elif line.startswith("data: "):
            current["data"] = json.loads(line[6:])
        elif line == "" and current:
            events.append(current)
            current = {}
    return events


def main() -> int:
    print("=" * 56)
    print("  M3 端到端检查：流式问答全流程")
    print("=" * 56)

    with httpx.Client(base_url=BASE, timeout=120) as c:
        # 0. 登录
        r = c.post(
            "/api/auth/login",
            json={"username": settings.admin_username, "password": settings.admin_password},
        )
        assert r.status_code == 200, r.text
        auth = {"Authorization": "Bearer " + r.json()["token"]}
        print("[1] 登录成功 ✓")

        # 1. 首次提问（自动建会话，SSE 流式）
        with c.stream(
            "POST", "/api/chat/stream", json={"question": "W1 耳机续航多久？"}, headers=auth
        ) as resp:
            assert resp.status_code == 200, resp.read()
            events = parse_sse(resp.iter_lines())
        names = [e["event"] for e in events]
        print(f"[2] SSE 事件流：{' → '.join(names)}")
        for required in ("meta", "citations", "delta", "done"):
            assert required in names, f"缺少 {required} 事件"
        meta = next(e["data"] for e in events if e["event"] == "meta")
        conv_id = meta["conversation_id"]
        answer = "".join(e["data"]["text"] for e in events if e["event"] == "delta")
        done = next(e["data"] for e in events if e["event"] == "done")
        cites = next(e["data"] for e in events if e["event"] == "citations")
        print(f"     答案 {len(answer)} 字 / {done['latency_ms']}ms / 引用 {len(cites)} 段")
        assert answer and len(cites) > 0

        # 2. 多轮追问（同一会话）
        with c.stream(
            "POST",
            "/api/chat/stream",
            json={"question": "那它防水吗？", "conversation_id": conv_id},
            headers=auth,
        ) as resp:
            events2 = parse_sse(resp.iter_lines())
        assert any(e["event"] == "done" for e in events2)
        print("[3] 多轮追问（同一会话）✓")

        # 3. 会话列表（标题自动命名 + 消息数）
        convs = c.get("/api/conversations", headers=auth).json()
        conv = next(x for x in convs if x["id"] == conv_id)
        assert conv["message_count"] == 4, conv
        print(f"[4] 会话「{conv['title']}」自动命名，消息数 {conv['message_count']} ✓")

        # 4. 消息列表 + 引用快照落库
        msgs = c.get(f"/api/conversations/{conv_id}/messages", headers=auth).json()
        assist = [m for m in msgs if m["role"] == "assistant"]
        assert len(assist) == 2 and len(assist[0]["citations"]) > 0
        print(f"[5] 消息落库：{len(msgs)} 条；引用快照完整（来源：{assist[0]['citations'][0]['filename']}）✓")

        # 5. 点赞
        r = c.put(f"/api/messages/{assist[0]['id']}/feedback", json={"feedback": "like"}, headers=auth)
        assert r.status_code == 200
        msgs = c.get(f"/api/conversations/{conv_id}/messages", headers=auth).json()
        saved = next(m for m in msgs if m["id"] == assist[0]["id"])
        assert saved["feedback"] == "like"
        print("[6] 点赞落库 ✓")

        # 6. 改名 + 导出 Markdown
        r = c.patch(f"/api/conversations/{conv_id}", json={"title": "耳机咨询"}, headers=auth)
        assert r.status_code == 200
        r = c.get(f"/api/conversations/{conv_id}/export", headers=auth)
        assert r.status_code == 200 and "耳机咨询" in r.text and "引用来源" in r.text
        print("[7] 改名 + Markdown 导出（含引用来源）✓")

        # 7. 删除会话（软删）
        r = c.delete(f"/api/conversations/{conv_id}", headers=auth)
        assert r.status_code == 200
        convs = c.get("/api/conversations", headers=auth).json()
        assert all(x["id"] != conv_id for x in convs)
        print("[8] 删除会话后列表不再显示 ✓")

        # 8. 防护：不存在的会话提问 → 404
        r = c.post(
            "/api/chat/stream", json={"question": "测试", "conversation_id": 999999}, headers=auth
        )
        assert r.status_code == 404
        print("[9] 不存在的会话被拒绝（404）✓")

        # 9. 防护：未登录提问 → 401
        r = c.post("/api/chat/stream", json={"question": "测试"})
        assert r.status_code == 401
        print("[10] 未登录提问被拒绝（401）✓")

    print()
    print("=" * 56)
    print("  M3 端到端检查全部通过")
    print("=" * 56)
    return 0


if __name__ == "__main__":
    sys.exit(main())
