# -*- coding: utf-8 -*-
"""
M2 端到端检查脚本（对着真实运行中的系统做全流程验证）

用途：服务启动后运行本脚本，它会走一遍真实操作路径：
    管理员登录 → 创建知识库 → 上传示例资料 → 等待后台处理完成 → 输出报告

跑法（在 backend 目录）：venv 的 python tests/e2e_m2_check.py
注意：需要系统正在运行（先双击 4-启动系统.bat，等浏览器打开后再跑本脚本）
"""
import os
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import httpx  # noqa: E402

from app.config import settings  # noqa: E402

# 目标服务地址（可用环境变量 RAG_BASE_URL 覆盖，默认本机 8000 端口）
BASE = os.environ.get("RAG_BASE_URL") or "http://127.0.0.1:8000"
KB_NAME = "电商商品知识库"


def main() -> int:
    print("=" * 56)
    print("  M2 端到端检查：登录 → 建库 → 上传 → 等待处理")
    print("=" * 56)

    with httpx.Client(base_url=BASE, timeout=60) as client:
        # 0. 服务在跑吗
        try:
            r = client.get("/api/health")
            r.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            print(f"[错误] 服务没有运行（{exc}），请先双击 4-启动系统.bat")
            return 1
        print("[1/6] 服务运行中 ✓")

        # 1. 管理员登录
        r = client.post(
            "/api/auth/login",
            json={"username": settings.admin_username, "password": settings.admin_password},
        )
        if r.status_code != 200:
            print(f"[错误] 管理员登录失败：{r.text}")
            return 1
        auth = {"Authorization": f"Bearer {r.json()['token']}"}
        print("[2/6] 管理员登录成功 ✓")

        # 2. 创建知识库（已存在则复用）
        r = client.get("/api/admin/kb", headers=auth)
        kbs = {kb["name"]: kb for kb in r.json()}
        if KB_NAME in kbs:
            kb = kbs[KB_NAME]
            print(f"[3/6] 知识库「{KB_NAME}」已存在（复用，id={kb['id']}）")
        else:
            r = client.post(
                "/api/admin/kb",
                json={"name": KB_NAME, "description": "示例数据：数码商品与售后政策"},
                headers=auth,
            )
            if r.status_code != 200:
                print(f"[错误] 创建知识库失败：{r.text}")
                return 1
            kb = r.json()
            print(f"[3/6] 知识库创建成功（id={kb['id']}）✓")

        # 3. 生成示例文件
        from scripts.seed_demo import _make_files  # 只生成文件，不碰数据库

        files = _make_files()
        print(f"[4/6] 已生成 {len(files)} 份示例文件 ✓")
        for name, _ in files:
            print(f"      · {name}")

        # 4. 上传
        import os

        from app.config import DATA_DIR

        demo_dir = DATA_DIR / "demo_docs"
        file_handles = [
            ("files", (name, open(demo_dir / name, "rb"), "application/octet-stream"))
            for name, _ in files
        ]
        try:
            r = client.post(f"/api/admin/kb/{kb['id']}/documents", files=file_handles, headers=auth)
        finally:
            for _, (_, fh, _ct) in file_handles:
                fh.close()
        if r.status_code != 200:
            print(f"[错误] 上传失败：{r.text}")
            return 1
        result = r.json()
        print(f"[5/6] 已上传 {len(result['saved'])} 份文件（后台开始处理）✓")
        for err in result.get("errors", []):
            print(f"      ⚠ {err}")

        # 5. 轮询处理状态
        print("[6/6] 等待处理完成（解析→分块→向量化）...")
        deadline = time.time() + 600
        while time.time() < deadline:
            r = client.get(f"/api/admin/kb/{kb['id']}/documents", headers=auth)
            docs = r.json()
            states = [d["status"] for d in docs]
            line = "  ".join(
                f"{d['filename'][:14]}:{d['status']}"
                + (f"({d['processed_chunks']}/{d['chunk_count']})"
                   if d["status"] == "processing" and d["chunk_count"] else "")
                for d in docs
            )
            print(f"\r      {line}          ", end="", flush=True)
            if all(s in ("ready", "failed") for s in states):
                break
            time.sleep(3)
        print()

        # 6. 结果报告
        r = client.get("/api/admin/kb", headers=auth)
        kb_now = next((k for k in r.json() if k["id"] == kb["id"]), None)
        r = client.get(f"/api/admin/kb/{kb['id']}/documents", headers=auth)
        docs = r.json()

        print()
        print("=" * 56)
        ok = sum(1 for d in docs if d["status"] == "ready")
        bad = [d for d in docs if d["status"] == "failed"]
        print(f"  结果：{ok}/{len(docs)} 份文档处理成功")
        if kb_now:
            print(f"  知识库合计：{kb_now['document_count']} 份文档 / {kb_now['chunk_count']} 个片段")
        for d in bad:
            print(f"  ✗ {d['filename']}：{d['error_msg']}")
        print("=" * 56)

        # 7. 演示账号（已存在则跳过）
        for name in ("demo", "demo2"):
            r = client.post(
                "/api/auth/register", json={"username": name, "password": "demo12345"}
            )
            if r.status_code == 200:
                print(f"  已创建演示账号：{name} / demo12345")
            elif "已被占用" in r.text:
                print(f"  演示账号已存在：{name}")
            else:
                print(f"  演示账号 {name} 创建失败：{r.text}")

    return 0 if ok == len(docs) and not bad else 1


if __name__ == "__main__":
    sys.exit(main())
