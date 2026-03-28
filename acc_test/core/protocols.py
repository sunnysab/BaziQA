from __future__ import annotations

from collections.abc import Sequence


def build_system_prompt(protocol: str) -> str:
    base = (
        "你是一名严谨的八字命理分析助手。"
        "你只能依据用户提供的固定命盘上下文和题目作答，"
        "不得凭空补充未提供的事实。"
        "每题最后一行必须输出“最终答案：X”。"
    )
    if protocol == "structured":
        return base + "本次评测要求你显式遵循量化扫描、冲突定级、应象映射三步。"
    if protocol == "multiturn":
        return base + "本次评测采用同一命主的多轮连续问答。"
    raise ValueError(f"Unsupported protocol: {protocol}")


def build_question_prompt(protocol: str, question: str, options: Sequence[str]) -> str:
    options_block = "\n".join(options)
    if protocol == "structured":
        return (
            "请严格按照以下三步进行分析，并只基于给定命盘上下文作答：\n"
            "1. 量化扫描：先判断日主强弱、五行分布、整体格局。\n"
            "2. 冲突定级：识别与当前问题最相关的冲合刑害、用忌神以及大运流年主导因素。\n"
            "3. 应象映射：将主导信号映射到题目选项，比较后给出唯一结论。\n\n"
            f"问题：{question}\n"
            f"{options_block}\n\n"
            "最后一行必须使用格式：最终答案：A"
        )

    if protocol == "multiturn":
        return (
            "请只基于给定命盘上下文分析下面的问题，并在最后一行给出唯一选项。\n\n"
            f"问题：{question}\n"
            f"{options_block}\n\n"
            "最后一行必须使用格式：最终答案：A"
        )

    raise ValueError(f"Unsupported protocol: {protocol}")
