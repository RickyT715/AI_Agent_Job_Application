"""Cover letter database model."""

from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class CoverLetter(Base, TimestampMixin):
    """Generated cover letter for a specific job match."""

    __tablename__ = "cover_letters"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    match_id: Mapped[int] = mapped_column(ForeignKey("match_results.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="cover_letters")
    match_result: Mapped["MatchResult"] = relationship()

    __table_args__ = (
        Index("ix_cover_letter_match_id", "match_id"),
    )
