"""Pydantic schemas for LinkedIn profile extraction."""

from pydantic import BaseModel, Field


class WorkExperience(BaseModel):
    """A single work experience entry."""

    title: str
    company: str
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None  # None means "Present"
    description: str = ""


class Education(BaseModel):
    """A single education entry."""

    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class Skill(BaseModel):
    """A skill from the profile."""

    name: str
    endorsements: int = 0


class LinkedInProfile(BaseModel):
    """Parsed LinkedIn profile data."""

    full_name: str = ""
    headline: str = ""
    location: str = ""
    email: str = ""
    phone: str = ""
    linkedin_url: str = ""
    summary: str = ""
    experience: list[WorkExperience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
