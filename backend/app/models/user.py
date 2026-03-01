"""User database model."""

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """Application user (single-user for now, multi-user ready)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    resume_text: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(50))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))

    # Structured profile data (populated from LinkedIn PDF or manual entry)
    skills_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    experience_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    education_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    certifications_json: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Relationships
    match_results: Mapped[list["MatchResult"]] = relationship(back_populates="user")
    applications: Mapped[list["Application"]] = relationship(back_populates="user")
    cover_letters: Mapped[list["CoverLetter"]] = relationship(back_populates="user")
