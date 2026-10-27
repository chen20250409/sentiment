from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Polarity = Literal["positive", "negative", "neutral"]


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000, description="待分析的评价文本")


class HitWordOut(BaseModel):
    word: str
    polarity: Polarity
    contribution: float
    position: int


class AnalyzeResponse(BaseModel):
    record_id: int
    polarity: Polarity
    confidence: float
    raw_score: float
    hit_words: list[HitWordOut]
    preview: str
    created_at: datetime


class RecordListItem(BaseModel):
    id: int
    preview: str
    polarity: Polarity
    confidence: float
    created_at: datetime


class RecordListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[RecordListItem]


class RecordDetail(RecordListItem):
    content: str
    raw_score: float
    hit_words: list[HitWordOut]


class HealthResponse(BaseModel):
    status: str
    version: str
    db: str
