# -*- coding: utf-8 -*-
"""
检索质量自检 —— 验证"知识能被找到"（问答功能的地基）

M4 升级版：走完整的混合检索链路（向量 + 关键词 → 融合 → 精排），
输出每个问题的精排相关度分数——用于校准相关性阈值、对比参数效果。

跑法（在 backend 目录，需先导入过示例数据，且系统服务已关闭）：
    RAG_DATA_DIR=F:\\LangchainRAG-data\\test-data python tests/check_retrieval.py
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.retrieval import retrieve  # noqa: E402

# (测试问题, 期望命中的来源文档 or None, 是否期望兜底)
QUESTIONS = [
    ("W1 耳机的续航时间是多久？", "商品资料-无线耳机W1.md", False),
    ("手表可以戴着游泳吗？", "商品资料-智能手表S2.docx", False),
    ("退货运费由谁承担？", "售后政策与常见问题.txt", False),
    ("扫地机器人的吸力有多大？", "扫地机器人R3参数.csv", False),
    ("三款商品的价格分别是多少？", "商品参数对比表.xlsx", False),
    ("耳机支持防水吗？", "商品资料-无线耳机W1.md", False),
    ("W1 防水等级是多少？", "商品资料-无线耳机W1.md", False),
    ("你们卖平板电脑吗？", None, True),  # 知识库没有的商品 → 应兜底
]


def main() -> int:
    print("=" * 60)
    print("  混合检索质量自检（向量 + 关键词 → 融合 → 精排）")
    print("=" * 60)

    passed = 0
    for question, expect_doc, expect_fallback in QUESTIONS:
        hits, is_fallback = retrieve(question)

        if expect_fallback:
            ok = is_fallback
            mark = "✓" if ok else "✗"
            detail = "正确兜底（未找到）" if is_fallback else "⚠ 未兜底，误报命中："
            print(f"\n{mark} 「{question}」→ {detail}")
            if not is_fallback:
                for h in hits[:3]:
                    print(f"     {h['filename']}  分数 {h['rerank_score']:.3f}")
        else:
            # 判定标准：期望来源文档出现在前 2 名内
            # （有些信息同时存在于多个文档，比如"防水"在耳机资料和参数对比表里都有）
            top2_files = [h["filename"] for h in hits[:2]]
            ok = (not is_fallback) and any(expect_doc in f for f in top2_files)
            mark = "✓" if ok else "✗"
            print(f"\n{mark} 「{question}」")
            if is_fallback:
                print("     ✗ 意外兜底（什么都没找到）")
            else:
                for h in hits:
                    flag = " ←" if expect_doc in h["filename"] else ""
                    print(f"     {h['filename']}  分数 {h['rerank_score']:.3f}{flag}")
        passed += int(ok)

    print()
    print("=" * 60)
    print(f"  结果：{passed}/{len(QUESTIONS)} 项符合预期")
    print("  （上面的分数用于校准 config 里的 rerank_threshold）")
    print("=" * 60)
    return 0 if passed == len(QUESTIONS) else 1


if __name__ == "__main__":
    sys.exit(main())
