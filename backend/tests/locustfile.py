# -*- coding: utf-8 -*-
r"""
LangchainRAG 压力测试脚本（Locust）

模拟两类用户：
  - ChatUser（占 80% 权重）：提问的用户——登录 → 反复提问（读取完整回答流）
  - BrowseUser（占 20% 权重）：翻阅的用户——登录 → 看会话列表 → 翻历史消息

阶梯加压（由 StressShape 控制）：10 人 → 25 人 → 50 人 → 100 人，逐档观察。

运行方式（在 backend 目录）：
    locust -f tests/locustfile.py --headless --host=http://127.0.0.1:8001

题库位置：默认读 RAG_DATA_DIR 下的 questions.json，
也可用环境变量 STRESS_QUESTIONS 指定。
"""
import json
import os
import random
import threading
from pathlib import Path

from locust import HttpUser, LoadTestShape, between, task

# ---- 配置 ----
STRESS_PASSWORD = "stress12345"
ACCOUNT_COUNT = 100
ACCOUNTS = [f"ptest{i:03d}" for i in range(1, ACCOUNT_COUNT + 1)]

_DEFAULT_QUESTIONS = Path(
    os.environ.get("STRESS_QUESTIONS")
    or r"F:\LangchainRAG-data\stress-data\questions.json"
)


def _load_questions() -> list[str]:
    try:
        return json.loads(_DEFAULT_QUESTIONS.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        # 题库缺失时用最小兜底，保证脚本能跑
        return ["W1 耳机续航多久？", "退货运费谁承担？", "S2 手表能游泳吗？"]


QUESTIONS = _load_questions()

# 账号池：每个虚拟用户登录时从池里"领"一个账号，用完还回去
_pool_lock = threading.Lock()
_account_pool = ACCOUNTS.copy()


def _take_account() -> str:
    with _pool_lock:
        if _account_pool:
            return _account_pool.pop()
        return random.choice(ACCOUNTS)  # 用户数超过账号数时复用


class BaseUser(HttpUser):
    """公共逻辑：登录并保持通行证"""

    abstract = True

    def on_start(self):
        self.token = None
        username = _take_account()
        with self.client.post(
            "/api/auth/login",
            json={"username": username, "password": STRESS_PASSWORD},
            name="/api/auth/login（登录）",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                self.token = resp.json()["token"]
                resp.success()
            else:
                resp.failure(f"登录失败 HTTP {resp.status_code}")
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}


class ChatUser(BaseUser):
    """提问型用户：读完整条回答流（包含检索 + 生成全过程）"""

    weight = 4
    wait_time = between(2, 6)  # 提问间隔（模拟真人：问完读一会儿再问）

    def on_start(self):
        super().on_start()
        self.conversation_id = None

    @task
    def ask(self):
        if not self.token:
            return

        # 10% 概率开一个新会话，90% 在当前会话里追问（贴近真实行为）
        if random.random() < 0.1:
            self.conversation_id = None
        payload = {"question": random.choice(QUESTIONS)}
        if self.conversation_id:
            payload["conversation_id"] = self.conversation_id

        with self.client.post(
            "/api/chat/stream",
            json=payload,
            headers=self.headers,
            stream=True,
            catch_response=True,
            name="/api/chat/stream（问答·完整回答）",
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"HTTP {resp.status_code}")
                return

            got_done = False
            expect_meta = False
            try:
                for raw in resp.iter_lines():
                    line = raw.decode("utf-8", "ignore") if isinstance(raw, bytes) else raw
                    if expect_meta and line.startswith("data: "):
                        try:
                            meta = json.loads(line[6:])
                            self.conversation_id = meta.get("conversation_id")
                        except (ValueError, TypeError):
                            pass
                        expect_meta = False
                    elif line == "event: meta":
                        expect_meta = True
                    elif line == "event: done":
                        got_done = True
                    elif line == "event: error":
                        resp.failure("服务端返回 error 事件")
                        return
                if got_done:
                    resp.success()
                else:
                    resp.failure("未收到 done 事件（回答被中断）")
            except Exception as exc:  # noqa: BLE001
                resp.failure(f"读取回答流出错：{exc}")


class BrowseUser(BaseUser):
    """浏览型用户：看列表、翻历史"""

    weight = 1
    wait_time = between(3, 8)

    @task(3)
    def list_conversations(self):
        if not self.token:
            return
        self.client.get(
            "/api/conversations",
            headers=self.headers,
            name="/api/conversations（会话列表）",
        )

    @task(2)
    def view_history(self):
        if not self.token:
            return
        resp = self.client.get(
            "/api/conversations",
            headers=self.headers,
            name="/api/conversations（会话列表）",
        )
        if resp.status_code == 200:
            convs = resp.json()
            if convs:
                cid = random.choice(convs)["id"]
                self.client.get(
                    f"/api/conversations/{cid}/messages",
                    headers=self.headers,
                    name="/api/conversations/[id]/messages（历史消息）",
                )


# 固定人数模式（用于真实 API 小规模验证）：
#   set STRESS_FIXED_USERS=10  set STRESS_FIXED_SECONDS=90
_FIXED_USERS = int(os.environ.get("STRESS_FIXED_USERS") or 0)
_FIXED_SECONDS = int(os.environ.get("STRESS_FIXED_SECONDS") or 120)


class StressShape(LoadTestShape):
    """
    阶梯加压曲线：10 → 25 → 50 → 100 人，每档稳定压 2~4 分钟后升档，
    最后在 100 人档观察 2 分钟后结束（总约 15 分钟）。

    设了环境变量 STRESS_FIXED_USERS 时切换为「固定人数模式」（用于小规模真实验证）。
    """

    stages = [
        {"duration": 150, "users": 10, "spawn_rate": 2},
        {"duration": 330, "users": 25, "spawn_rate": 3},
        {"duration": 570, "users": 50, "spawn_rate": 5},
        {"duration": 780, "users": 100, "spawn_rate": 10},
        {"duration": 900, "users": 100, "spawn_rate": 10},
    ]

    def tick(self):
        run_time = self.get_run_time()
        if _FIXED_USERS:
            if run_time < _FIXED_SECONDS:
                return (_FIXED_USERS, max(1, _FIXED_USERS // 10))
            return None
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        return None  # 曲线结束，压测自动停止
