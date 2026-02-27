"""Job posting database model."""

from sqlalchemy import JSON, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Job(Base, TimestampMixin):
    """Stored job posting from any scraping source."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    workplace_type: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str | None] = mapped_column(Text)
    salary_min: Mapped[int | None] = mapped_column()
    salary_max: Mapped[int | None] = mapped_column()
    salary_currency: Mapped[str | None] = mapped_column(String(10))
    employment_type: Mapped[str | None] = mapped_column(String(50))
    experience_level: Mapped[str | None] = mapped_column(String(50))
    apply_url: Mapped[str | None] = mapped_column(String(2000))
    raw_data: Mapped[dict | None] = mapped_column(JSON)

    # Relationships
    match_results: Mapped[list["MatchResult"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_job_external_source", "external_id", "source", unique=True),
    )
