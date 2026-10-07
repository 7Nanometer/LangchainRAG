# -*- coding: utf-8 -*-
"""问答提示词模板（改回答风格/规则只需改这个文件）"""
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

SYSTEM_PROMPT = """你是「知识库智能客服」，负责根据商品知识库资料，回答用户关于商品的问题。

回答规则（必须严格遵守）：
1. 只依据【参考资料】中的内容回答，绝不编造资料里没有的信息
2. 如果回答中用到了某段资料，请在该内容后面标注对应编号，例如 [1] 或 [1][2]
3. 如果【参考资料】无法回答问题，礼貌地告知用户知识库里暂时没有相关信息，
   建议换个说法再问或联系人工客服——宁可说不知道，也不要瞎编
4. 用简体中文回答，语气像专业客服：简洁、友好、条理清晰
5. 涉及数字、参数、价格、政策条款时，必须与资料完全一致，不得改动
6. 回答里不要出现"参考资料""文档中"这类字眼，自然地组织语言"""

# 兜底回答的提示词（适合"知识库里没找到相关内容"的场景）
FALLBACK_HINT = """本次的问题在知识库中没有检索到相关资料。

请用客服的口吻回复用户：
1. 说明知识库中暂时没有找到与问题相关的内容
2. 建议用户换个说法再问，或联系人工客服
3. 不要编造任何信息"""


def build_qa_messages(
    question: str,
    hits: list[dict],
    history: list[tuple[str, str]] | None = None,
    fallback_extra: str | None = None,
) -> list:
    """
    组装发给大模型的消息列表。

    question: 用户本次的提问
    hits:     检索到的资料片段 [{index, filename, content}, ...]
    history:  最近几轮对话 [(role, content), ...]（role: user / assistant）
    fallback_extra: 兜底时附加的信息（如"知识库当前收录了哪些资料"）
    """
    if hits:
        context = "\n\n".join(
            f"[{h['index']}] 来源：{h['filename']}\n{h['content']}" for h in hits
        )
        user_content = f"【参考资料】\n{context}\n\n【用户问题】\n{question}"
    else:
        # 没有检索到资料：直接把"没资料"作为事实交给模型组织语言
        hint = FALLBACK_HINT
        if fallback_extra:
            hint += f"\n4. 可以顺带告诉用户：知识库当前收录的资料包括：{fallback_extra}"
        user_content = f"【提示】{hint}\n\n【用户问题】\n{question}"

    messages: list = [SystemMessage(content=SYSTEM_PROMPT)]
    for role, content in history or []:
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=user_content))
    return messages
