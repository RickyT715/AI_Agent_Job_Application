"""Match result database model."""

from sqlalchemy import JSON, Float, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class MatchResult(Base, TimestampMixin):
    """Scoring result from the matching pipeline."""

    __tablename__ = "match_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    overall_score: Mapped[float] = mapped_column(nullable=False)
    score_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    strengths: Mapped[list] = mapped_column(JSON, nullable=False)
    missing_skills: Mapped[list] = mapped_column(JSON, nullable=False)
    interview_talking_points: Mapped[list] = mapped_column(JSON, default=list)

    # New scoring fields (all nullable for backward compatibility)
    ats_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ats_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    requirement_matches: Mapped[list | None] = mapped_column(JSON, nullable=True)
    requirements_met_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    integrated_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="match_results")
    job: Mapped["Job"] = relationship(back_populates="match_results")

    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_match_user_job"),
        Index("ix_match_user_score", "user_id", "overall_score"),
    )
