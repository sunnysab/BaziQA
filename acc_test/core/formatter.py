from __future__ import annotations


def format_bazi_context(
    *,
    anonymous_id: str,
    gender: str,
    birth_raw: str,
    raw_output: str,
) -> str:
    return (
        "【八字排盘结果】\n\n"
        f"命主：{anonymous_id}\n"
        f"性别：{gender}\n"
        f"出生信息：{birth_raw}\n\n"
        "【本地排盘输出】\n"
        f"{raw_output.strip()}\n"
    )
