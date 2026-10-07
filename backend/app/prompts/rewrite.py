# -*- coding: utf-8 -*-
"""多轮对话的「指代改写」提示词

解决什么问题：用户追问"那它防水吗？"时，单独这句话检索不到资料
（不知道"它"是谁）。先让模型把它补全成"W1 耳机防水吗？"，再去检索就准了。
"""
from langchain_core.messages import HumanMessage, SystemMessage

REWRITE_SYSTEM = """你是检索助手。请根据对话历史，把用户的最新问题改写成一个"可以独立检索"的完整问题。

改写规则：
1. 把"它、这个、那个、这款、上面说的"等代词，替换成对话历史里提到的具体商品名或主题
2. 补全省略的对象，但绝不能添加对话历史中没有出现过的信息
3. 如果最新问题本身已经完整（比如本来就包含商品名），原样输出
4. 只输出改写后的问题本身，不要任何解释、引号装饰或换行"""


def build_rewrite_messages(question: str, history: list[tuple[str, str]]) -> list:
    """history: [(role, content), ...]（role: user / assistant）"""
    hist_lines = []
    for role, content in history:
        speaker = "用户" if role == "user" else "客服"
        hist_lines.append(f"{speaker}：{content[:200]}")
    hist_text = "\n".join(hist_lines)

    return [
        SystemMessage(content=REWRITE_SYSTEM),
        HumanMessage(
            content=(
                f"【对话历史】\n{hist_text}\n\n"
                f"【用户的最新问题】\n{question}\n\n"
                "请输出改写后的检索问句："
            )
        ),
    ]
