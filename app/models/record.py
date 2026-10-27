import sqlalchemy as sa
from sqlalchemy.dialects.mysql import DATETIME

from app.db.base import Base


class SentimentRecord(Base):
    """评价情绪分析记录：原文 / 结果 / 时间（对应需求三要素）"""

    __tablename__ = "sentiment_record"

    id = sa.Column(
        sa.BigInteger().with_variant(sa.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    content = sa.Column(sa.Text, nullable=False, comment="原文")
    preview = sa.Column(sa.String(120), nullable=False, comment="列表页摘要，避免读大字段")
    polarity = sa.Column(
        sa.Enum("positive", "negative", "neutral", name="polarity_enum"),
        nullable=False,
        comment="情绪标签",
    )
    confidence = sa.Column(sa.Numeric(5, 4), nullable=False, comment="置信度 0~1")
    raw_score = sa.Column(
        sa.Numeric(8, 3), nullable=False, server_default=sa.text("0"), comment="词典原始分"
    )
    hit_words = sa.Column(sa.JSON, nullable=True, comment="命中词与贡献分（可解释性）")
    created_at = sa.Column(
        sa.DateTime().with_variant(DATETIME(fsp=3), "mysql"),
        nullable=False,
        server_default=sa.func.now(),
        comment="分析时间",
    )

    __table_args__ = (
        sa.Index("idx_created_id", "created_at", "id"),
        sa.Index("idx_polarity_created", "polarity", "created_at"),
    )
