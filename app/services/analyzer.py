"""情感分析引擎：中文情感词典 + 规则打分。

流程：预处理 → 按标点切句 → 句内正向最大匹配情感词 →
程度副词加权 / 否定词翻转极性 → 汇总 raw_score → 三分类 + 置信度。
"""
from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import get_settings

LEXICON_DIR = Path(__file__).resolve().parent.parent / "lexicon"

_SENT_RE = re.compile(r"[^。！？!?；;…\r\n]+")
_URL_RE = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)
_WS_RE = re.compile(r"\s+")

MOD_WINDOW = 6  # 情感词向前查找程度副词/否定词的窗口长度
EXCLAIM_FACTOR = 1.2  # 感叹号句增强系数


@dataclass
class HitWord:
    word: str
    polarity: str
    contribution: float
    position: int


@dataclass
class AnalysisOutcome:
    polarity: str
    confidence: float
    raw_score: float
    hit_words: list[dict[str, Any]]


def _read_words(name: str) -> set[str]:
    path = LEXICON_DIR / name
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }


@lru_cache(maxsize=1)
def _load_lexicon() -> tuple[dict[str, float], dict[str, float], set[str], int]:
    positive = _read_words("positive.txt")
    negative = _read_words("negative.txt")
    negation = _read_words("negation.txt")

    degree: dict[str, float] = {}
    for line in (LEXICON_DIR / "degree.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            try:
                degree[parts[0]] = float(parts[1])
            except ValueError:
                continue

    sentiment: dict[str, float] = {w: 1.0 for w in positive}
    for w in negative:
        sentiment[w] = -1.0
    max_len = max(len(w) for w in sentiment)
    return sentiment, degree, negation, max_len


def _dedup(words: list[str]) -> list[str]:
    """去掉被更长命中的词包含的短词（如「不太」命中时不再计「不」）。"""
    return [w for w in words if not any(w != o and w in o for o in words)]


def _match(sentence: str, sentiment: dict[str, float], max_len: int):
    """句内正向最大匹配，返回 [(word, start, length)]。"""
    hits = []
    i, n = 0, len(sentence)
    while i < n:
        found = None
        for length in range(min(max_len, n - i), 0, -1):
            w = sentence[i : i + length]
            if w in sentiment:
                found = (w, i, length)
                break
        if found:
            hits.append(found)
            i += found[2]
        else:
            i += 1
    return hits


def _window_mods(sentence: str, start: int, search_from: int, degree: dict[str, float], negation: set[str]):
    """查看情感词前窗口内的程度副词与否定词。

    search_from：同一句中上一个已消费情感词的结束位置，
    避免把上一个词内部的「不/没」误当作本词的否定修饰。
    """
    s = max(search_from, start - MOD_WINDOW)
    window = sentence[s:start]
    deg = 1.0
    flip = False
    if window:
        found_deg = _dedup([w for w in degree if w in window])
        if found_deg:
            deg = max(degree[w] for w in found_deg)
        # 否定词若是某个程度词的子串（如「几乎不」含「不」）则不计，避免重复翻转
        found_neg = [
            w for w in negation if w in window and not any(w != d and w in d for d in found_deg)
        ]
        flip = len(_dedup(found_neg)) % 2 == 1
    return deg, flip


def analyze_text(text: str) -> AnalysisOutcome:
    settings = get_settings()
    sentiment, degree, negation, max_len = _load_lexicon()

    cleaned = _WS_RE.sub("", _URL_RE.sub("", text))
    raw = 0.0
    hits: list[HitWord] = []

    for m in _SENT_RE.finditer(cleaned):
        sentence = m.group()
        base = m.start()
        exclam = sentence.endswith(("!", "！"))
        prev_end = 0
        for w, i, length in _match(sentence, sentiment, max_len):
            pol = sentiment[w]
            deg, flip = _window_mods(sentence, i, prev_end, degree, negation)
            contrib = pol * deg * (-1.0 if flip else 1.0) * (EXCLAIM_FACTOR if exclam else 1.0)
            raw += contrib
            hits.append(
                HitWord(
                    word=w,
                    polarity="positive" if pol > 0 else "negative",
                    contribution=round(contrib, 3),
                    position=base + i,
                )
            )
            prev_end = i + length

    raw = round(raw, 3)
    if raw > settings.pos_threshold:
        polarity = "positive"
        confidence = min(0.99, round(1.0 - math.exp(-abs(raw) / settings.conf_scale), 4))
    elif raw < settings.neg_threshold:
        polarity = "negative"
        confidence = min(0.99, round(1.0 - math.exp(-abs(raw) / settings.conf_scale), 4))
    else:
        polarity = "neutral"
        confidence = round(1.0 / (1.0 + abs(raw)), 4)

    return AnalysisOutcome(
        polarity=polarity,
        confidence=confidence,
        raw_score=raw,
        hit_words=[asdict(h) for h in hits],
    )
