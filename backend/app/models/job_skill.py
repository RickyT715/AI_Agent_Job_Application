"""Per-job extracted skill database model."""

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class JobSkill(Base, TimestampMixin):
    """A single skill extracted from a job posting."""

    __tablename__ = "job_skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # "technical" or "soft_skill"

    # Relationships
    job: Mapped["Job"] = relationship(back_populates="skills")

    __table_args__ = (
        UniqueConstraint("job_id", "skill_name", name="uq_job_skill"),
        Index("ix_job_skill_skill_name", "skill_name"),
        Index("ix_job_skill_job_id", "job_id"),
        Index("ix_job_skill_category", "category"),
    )
