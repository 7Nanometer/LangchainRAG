# -*- coding: utf-8 -*-
r"""
压测环境准备（一次性脚本）

做三件事：
  1. 向压测数据环境导入示例知识库（走真实入库流水线）
  2. 批量创建 100 个压测账号（ptest001 ~ ptest100，统一密码 stress12345）
  3. 生成压测题库（120 条多样化问题，降低缓存全命中的概率）

用法（在 backend 目录）：
    set RAG_DATA_DIR=F:\LangchainRAG-data\stress-data
    python scripts\stress_prepare.py
建议加 MODEL_DEVICE=cpu 运行（避免与正在使用的正式系统抢显卡）
"""
import json
import random
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.config import DATA_DIR  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Document, KnowledgeBase, User  # noqa: E402

ACCOUNT_COUNT = 100
STRESS_PASSWORD = "stress12345"
STRESS_KB_NAME = "压测知识库"

# ---------------------------------------------------------------------------
# 压测题库：60 条基础问题（覆盖命中/参数/售后/兜底）+ 60 条变体 = 120 条
# ---------------------------------------------------------------------------

_BASE_QUESTIONS = [
    # —— W1 耳机 ——
    "W1 耳机的续航时间是多久？",
    "W1 开降噪能用多长时间？",
    "W1 耳机支持快充吗？充多久能用？",
    "W1 的防水等级是多少？",
    "W1 耳机防汗吗？运动能戴吗？",
    "W1 用什么充电接口？",
    "W1 支持无线充电吗？",
    "W1 的降噪深度是多少？",
    "W1 支持同时连接两个设备吗？",
    "W1 耳机单只重量多少？",
    "W1 有几种颜色？",
    "W1 支持什么音频编码？",
    "W1 耳机包装里有哪些东西？",
    "W1 保修多久？",
    "W1 售价多少钱？",
    # —— S2 手表 ——
    "S2 手表续航几天？",
    "S2 手表可以戴着游泳吗？",
    "S2 屏幕多大？",
    "S2 支持血氧监测吗？",
    "S2 手表重量多少？",
    "S2 支持哪些运动模式？",
    "S2 防水等级是多少？",
    "S2 售价多少？",
    "S2 支持 iOS 吗？",
    "S2 怎么充电？充满要多久？",
    "S2 表带可以换吗？",
    "S2 有 GPS 吗？",
    # —— R3 扫地机器人 ——
    "R3 扫地机器人的吸力多大？",
    "R3 噪音大不大？",
    "R3 电池容量多少？",
    "R3 边扫边拖吗？",
    "R3 机身高度多少？",
    "R3 怎么导航的？",
    "R3 充满电能用多久？",
    "R3 售价多少？",
    "R3 会自动回充吗？",
    "R3 能连手机 App 吗？",
    # —— 售后政策 ——
    "退货政策是怎样的？",
    "7 天无理由退货有什么条件？",
    "退货运费谁承担？",
    "保修期是多久？",
    "人为损坏保修吗？",
    "发票怎么开？",
    "多久能发货？",
    "可以修改收货地址吗？",
    "支持哪些付款方式？",
    "质量问题怎么换货？",
    "过保修期了怎么办？",
    "满多少包邮？",
    "售后申请在哪里提交？",
    # —— 对比与兜底 ——
    "三款商品的价格分别是多少？",
    "耳机和手表哪个更值得买？",
    "你们卖平板电脑吗？",
    "有没有优惠活动？",
    "支持以旧换新吗？",
    "哪个产品防水最好？",
    "你们有线下门店吗？",
    "能货到付款吗？",
    "双十一有折扣吗？",
    "推荐一款送人的产品",
]

_PREFIXES = ["请问，", "麻烦问下，", "想了解一下，", "帮我查查，", "问一下，", "", "", ""]


def build_question_bank(seed: int = 42) -> list[str]:
    rnd = random.Random(seed)
    extra = [rnd.choice(_PREFIXES) + q for q in rnd.sample(_BASE_QUESTIONS, 60)]
    return _BASE_QUESTIONS + extra


def main() -> int:
    print("=" * 56)
    print("  压测环境准备")
    print(f"  数据目录：{DATA_DIR}")
    print("=" * 56)
    if "stress-data" not in str(DATA_DIR):
        print("[安全拦截] 数据目录不是 stress-data，拒绝执行（防止污染正式数据）")
        return 1

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # ---- 1. 导入示例知识库 ----
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.name == STRESS_KB_NAME).first()
        if kb is None:
            from scripts.seed_demo import _make_files  # 复用示例文件生成

            files = _make_files()
            kb = KnowledgeBase(name=STRESS_KB_NAME, description="压力测试数据")
            db.add(kb)
            db.commit()
            db.refresh(kb)

            from app.services.ingestion_service import process_document

            print("\n[1/3] 导入知识库（首次约需几分钟）...")
            for name, ftype in files:
                path = DATA_DIR / "demo_docs" / name
                doc = Document(
                    kb_id=kb.id, filename=name, file_path=str(path),
                    file_type=ftype, size_bytes=path.stat().st_size, status="pending",
                )
                db.add(doc)
                db.commit()
                db.refresh(doc)
                process_document(doc.id)
                db.refresh(doc)
                print(f"      {name} → {doc.status}（{doc.chunk_count} 段）")
        else:
            print("\n[1/3] 知识库已存在，跳过导入")

        # ---- 2. 批量创建压测账号 ----
        print(f"\n[2/3] 创建 {ACCOUNT_COUNT} 个压测账号（ptest001 ~ ptest{ACCOUNT_COUNT:03d}）...")
        created = 0
        password_hash = hash_password(STRESS_PASSWORD)  # 同一个密码只算一次哈希
        for i in range(1, ACCOUNT_COUNT + 1):
            username = f"ptest{i:03d}"
            if db.query(User).filter(User.username == username).first() is None:
                db.add(User(username=username, password_hash=password_hash, role="user"))
                created += 1
        db.commit()
        print(f"      新建 {created} 个（已存在的跳过）")

        # ---- 3. 生成题库 ----
        questions = build_question_bank()
        qfile = DATA_DIR / "questions.json"
        qfile.write_text(json.dumps(questions, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n[3/3] 题库已生成：{len(questions)} 条 → {qfile}")

        print()
        print("=" * 56)
        print("  压测环境准备完成")
        print("=" * 56)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
