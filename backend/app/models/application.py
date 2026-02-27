"""Application tracking database model."""

from sqlalchemy import JSON, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Application(Base, TimestampMixin):
    """Tracks a job application submitted by the agent."""

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # pending, in_progress, submitted, failed, rejected
    ats_platform: Mapped[str | None] = mapped_column(String(50))
    apply_url: Mapped[str | None] = mapped_column(String(2000))
    fields_filled: Mapped[dict | None] = mapped_column(JSON)
    screenshot_b64: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="applications")
    job: Mapped["Job"] = relationship(back_populates="applications")

    __table_args__ = (
        Index("ix_application_user_id", "user_id"),
        Index("ix_application_job_id", "job_id"),
    )
