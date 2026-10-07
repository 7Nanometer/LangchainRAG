# -*- coding: utf-8 -*-
"""
检索质量自检 —— 验证"知识能被按意思找到"（问答功能的地基）

用几个典型问题去向量库里检索，检查返回的片段是否来自正确的文档。
调增大/减小分块尺寸、换模型等参数后，都可以跑一下本脚本对比效果。

跑法（在 backend 目录，需先导入过示例数据）：
    RAG_DATA_DIR=F:\\LangchainRAG-data\\test-data python tests/check_retrieval.py
（不设 RAG_DATA_DIR 则使用正式数据目录；运行前请确保系统服务已关闭）
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.embeddings import get_embeddings  # noqa: E402
from app.services.vectorstore import search_by_vector  # noqa: E402

# (测试问题, 期望命中的来源文档)
QUESTIONS = [
    ("W1 耳机的续航时间是多久？", "商品资料-无线耳机W1.md"),
    ("手表可以戴着游泳吗？", "商品资料-智能手表S2.docx"),
    ("退货运费由谁承担？", "售后政策与常见问题.txt"),
    ("扫地机器人的吸力有多大？", "扫地机器人R3参数.csv"),
    ("三款商品的价格分别是多少？", "商品参数对比表.xlsx"),
    ("耳机支持防水吗？", "商品资料-无线耳机W1.md"),
]


def _extract_source(text: str) -> str:
    """从片段内容里解析来源文件名（片段头部格式：【文档：xxx】）"""
    if text.startswith("【文档："):
        return text.split("】", 1)[0].replace("【文档：", "")
    return "?"


def main() -> int:
    print("=" * 56)
    print("  检索质量自检（向量检索 Top3）")
    print("=" * 56)

    emb = get_embeddings()
    hit = 0
    for question, expect in QUESTIONS:
        vector = emb.embed_query(question)
        results = search_by_vector(vector, k=3)
        sources = [_extract_source(r["text"]) for r in results]
        ok = expect in sources
        hit += int(ok)
        mark = "✓" if ok else "✗"
        print(f"\n{mark} 「{question}」")
        print(f"   期望来源：{expect}")
        for r, src in zip(results, sources):
            flag = " ←" if src == expect else ""
            print(f"   Top{results.index(r) + 1}：{src}（距离 {r['distance']:.3f}）{flag}")
        if not ok:
            print("   ⚠ 没有找到期望的来源文档，可能需要检查分块或模型设置")

    print()
    print("=" * 56)
    print(f"  结果：{hit}/{len(QUESTIONS)} 个问题命中了正确的来源文档")
    print("=" * 56)
    return 0 if hit == len(QUESTIONS) else 1


if __name__ == "__main__":
    sys.exit(main())
