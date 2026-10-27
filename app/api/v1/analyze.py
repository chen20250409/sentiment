from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.record import SentimentRecord
from app.schemas.sentiment import AnalyzeRequest, AnalyzeResponse, HitWordOut
from app.services.analyzer import analyze_text

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    outcome = analyze_text(payload.text)
    record = SentimentRecord(
        content=payload.text,
        preview=payload.text[:120],
        polarity=outcome.polarity,
        confidence=Decimal(str(outcome.confidence)),
        raw_score=Decimal(str(outcome.raw_score)),
        hit_words=outcome.hit_words,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return AnalyzeResponse(
        record_id=record.id,
        polarity=outcome.polarity,
        confidence=outcome.confidence,
        raw_score=outcome.raw_score,
        hit_words=[HitWordOut(**h) for h in outcome.hit_words],
        preview=record.preview,
        created_at=record.created_at,
    )
