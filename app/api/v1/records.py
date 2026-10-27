from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.record import SentimentRecord
from app.schemas.sentiment import (
    RecordDetail,
    RecordListItem,
    RecordListResponse,
)

router = APIRouter()


def _apply_filters(stmt, polarity: str | None, date_from: date | None, date_to: date | None, q: str | None):
    if polarity:
        stmt = stmt.where(SentimentRecord.polarity == polarity)
    if date_from:
        stmt = stmt.where(SentimentRecord.created_at >= datetime.combine(date_from, time.min))
    if date_to:
        stmt = stmt.where(SentimentRecord.created_at < datetime.combine(date_to + timedelta(days=1), time.min))
    if q:
        kw = f"%{q}%"
        stmt = stmt.where(or_(SentimentRecord.preview.like(kw), SentimentRecord.content.like(kw)))
    return stmt


@router.get("/records", response_model=RecordListResponse)
async def list_records(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    polarity: str | None = Query(None, pattern="^(positive|negative|neutral)$"),
    date_from: date | None = None,
    date_to: date | None = None,
    q: str | None = Query(None, max_length=100),
    db: AsyncSession = Depends(get_db),
):
    base = _apply_filters(select(SentimentRecord), polarity, date_from, date_to, q)

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()

    stmt = _apply_filters(
        select(
            SentimentRecord.id,
            SentimentRecord.preview,
            SentimentRecord.polarity,
            SentimentRecord.confidence,
            SentimentRecord.created_at,
        ),
        polarity,
        date_from,
        date_to,
        q,
    )
    stmt = stmt.order_by(SentimentRecord.created_at.desc(), SentimentRecord.id.desc())
    stmt = stmt.offset((page - 1) * size).limit(size)
    rows = (await db.execute(stmt)).all()

    return RecordListResponse(
        total=total,
        page=page,
        size=size,
        items=[
            RecordListItem(
                id=r.id,
                preview=r.preview,
                polarity=r.polarity,
                confidence=float(r.confidence),
                created_at=r.created_at,
            )
            for r in rows
        ],
    )


async def _get_or_404(record_id: int, db: AsyncSession) -> SentimentRecord:
    record = await db.get(SentimentRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


@router.get("/records/{record_id}", response_model=RecordDetail)
async def get_record(record_id: int, db: AsyncSession = Depends(get_db)):
    record = await _get_or_404(record_id, db)
    return RecordDetail(
        id=record.id,
        preview=record.preview,
        polarity=record.polarity,
        confidence=float(record.confidence),
        created_at=record.created_at,
        content=record.content,
        raw_score=float(record.raw_score),
        hit_words=record.hit_words or [],
    )


@router.delete("/records/{record_id}", status_code=204)
async def delete_record(record_id: int, db: AsyncSession = Depends(get_db)):
    record = await _get_or_404(record_id, db)
    await db.delete(record)
    await db.commit()
