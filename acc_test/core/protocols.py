from __future__ import annotations

from collections.abc import Sequence


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
