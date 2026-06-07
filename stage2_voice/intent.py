"""
英文口语短句 → 动作名的关键词模糊匹配。
"""

from __future__ import annotations

from typing import Optional

# 动作 → 触发关键词
_KEYWORDS: dict[str, list[str]] = {
    "wake": ["wake up", "wake", "get up", "rise"],
    "handshake": ["shake hand", "shake", "handshake", "hand shake", "hand"],
    "again": ["again", "one more", "do it again", "once more"],
    "happy": ["good boy", "good", "great", "well done", "happy", "good job"],
    "shy": ["be shy", "shy", "oh no", "hide", "shy back", "shy shy"],
    "sleep": ["go to sleep", "sleep", "good night", "night", "rest", "sleepy"],
}

_GREETINGS = ["hello", "hi", "hey", "quanquan", "quan quan"]


def match(text: str) -> Optional[tuple[str, str]]:
    """
    英文文本 → (action_name, response_phrase)。

    两层匹配：先精确子串，再分词重叠。
    均失败返回 None。
    """
    lowered = text.strip().lower().rstrip(".!?,;:")
    if not lowered:
        return None

    # 第一轮：精确子串匹配
    for action_name, phrases in _KEYWORDS.items():
        for phrase in phrases:
            if phrase in lowered:
                return _build(action_name)

    # 第二轮：分词重叠匹配（容忍个别词识别偏差）
    words = set(lowered.split())
    for action_name, phrases in _KEYWORDS.items():
        for phrase in phrases:
            phrase_words = set(phrase.split())
            if len(phrase_words) >= 2:
                overlap = phrase_words & words
                if len(overlap) >= max(2, len(phrase_words) * 2 // 3):
                    return _build(action_name)
            elif len(phrase_words) == 1:
                if phrase in words:
                    return _build(action_name)

    # greeting 回退（只匹配完整单词）
    for phrase in _GREETINGS:
        if set(phrase.split()) & words:
            return _build("greeting")

    return None


def _build(action_name: str) -> tuple[str, str]:
    from speech_out import RESPONSES
    response = RESPONSES.get(action_name, RESPONSES.get("unknown", "Okay!"))
    return (action_name, response)
