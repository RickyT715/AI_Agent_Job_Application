"""LLM-as-Judge scoring using Claude Sonnet with structured output.

Scores job-resume matches on multiple dimensions using Claude's reasoning.
Includes a lightweight quick_score() for fast relevance pre-screening.
"""

import json
import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from app.schemas.matching import JobMatchScore

logger = logging.getLogger(__name__)

SCORING_PROMPT = ChatPromptTemplate.from_messages([
    (
        "human",
        """You are an expert job matching analyst. Score how well a candidate's resume \
matches a job posting on multiple dimensions. Be precise and actionable in your \
reasoning. Score each dimension from 1 (poor match) to 10 (perfect match).

## Target Role Context
The candidate is targeting: {target_role} positions
Candidate Experience Level: {experience_level}
Preferred Workplace: {workplace_types}

Evaluate this resume against the job posting.

## Resume
{resume_text}

## Job Posting
Title: {job_title}
Company: {job_company}
Location: {job_location}
Description: {job_description}
Requirements: {job_requirements}
Salary Range: {job_salary}

## Candidate Preferences
Preferred Locations: {preferred_locations}
Salary Range: {salary_range}

## Step 1: Requirement Extraction & Matching
Extract every distinct requirement from the job posting (from both description and \
requirements sections). For each requirement, determine if the candidate meets it.

Categorize each requirement as one of:
- "technical_skill" — specific language, framework, tool, or technology
- "soft_skill" — communication, leadership, collaboration, etc.
- "experience" — years of experience or domain-specific experience
- "education" — degree requirements
- "certification" — specific certifications (AWS, PMP, etc.)
- "other" — anything else

For each, provide:
- requirement: the requirement text
- category: one of the categories above
- met: true/false
- evidence: brief evidence from the resume, or "Not found"
- confidence: 0.0-1.0 how confident you are

Also compute requirements_met_ratio as the fraction of requirements met (0.0-1.0).

## Step 2: Dimension Scoring
Use these exact weights for overall_score:
- skills ({skills_weight}%): How well do the candidate's skills match the requirements?
- experience ({experience_weight}%): Does the experience level and years match?
- education ({education_weight}%): Does education background align?
- location ({location_weight}%): Is the location compatible with preferences?
- salary ({salary_weight}%): Does the salary range match expectations?

Calculate overall_score as:
(skills × {skills_weight} + experience × {experience_weight} +
education × {education_weight} + location × {location_weight} +
salary × {salary_weight}) / 100

## Step 3: Analysis
Also provide:
- reasoning: 2-3 sentence explanation of the match quality
- strengths: List of matching strengths
- missing_skills: Skills the job requires that the candidate lacks
- interview_talking_points: Key points the candidate should emphasize""",
    ),
])

QUICK_SCORE_PROMPT = ChatPromptTemplate.from_messages([
    (
        "human",
        """Rate 1-10 how relevant this job is for the candidate. Consider:
- Does the role type match their target ({target_role})?
- Are the core technical skills aligned?
- Is the seniority level appropriate for someone with {experience_level} experience?

Resume (key skills): {resume_summary}
Job: {job_title} at {job_company}
Brief: {job_brief}

Return ONLY valid JSON: {{"relevance": <int 1-10>, "reason": "<15 words max>"}}""",
    ),
])


class JobScorer:
    """Scores job-resume matches using Claude as LLM-as-Judge."""

    def __init__(self, llm: BaseChatModel) -> None:
        self._llm = llm
        self._structured_llm = self._llm.with_structured_output(JobMatchScore)

    async def score(
        self,
        resume_text: str,
        job_title: str,
        job_company: str,
        job_description: str,
        job_location: str = "Not specified",
        job_requirements: str = "Not specified",
        job_salary: str = "Not specified",
        preferred_locations: str = "Any",
        salary_range: str = "Not specified",
        target_role: str = "Software Engineer",
        experience_level: str = "mid",
        workplace_types: str = "remote, hybrid",
        weights: dict[str, int] | None = None,
    ) -> JobMatchScore:
        """Score a single job-resume match.

        Args:
            resume_text: Full resume text.
            job_title: Job title.
            job_company: Company name.
            job_description: Full job description.
            job_location: Job location string.
            job_requirements: Job requirements text.
            job_salary: Job salary range string.
            preferred_locations: User's preferred locations.
            salary_range: User's desired salary range.
            target_role: The role the user is searching for.
            experience_level: User's experience level (entry/mid/senior/lead).
            workplace_types: User's workplace preferences.
            weights: Scoring weights as percentages (e.g. {"skills": 35, ...}).

        Returns:
            JobMatchScore with dimension scores, reasoning, and recommendations.
        """
        if weights is None:
            weights = {
                "skills": 35,
                "experience": 25,
                "education": 15,
                "location": 15,
                "salary": 10,
            }

        prompt_value = await SCORING_PROMPT.ainvoke({
            "resume_text": resume_text,
            "job_title": job_title,
            "job_company": job_company,
            "job_location": job_location,
            "job_description": job_description,
            "job_requirements": job_requirements,
            "job_salary": job_salary,
            "preferred_locations": preferred_locations,
            "salary_range": salary_range,
            "target_role": target_role,
            "experience_level": experience_level,
            "workplace_types": workplace_types,
            "skills_weight": weights["skills"],
            "experience_weight": weights["experience"],
            "education_weight": weights["education"],
            "location_weight": weights["location"],
            "salary_weight": weights["salary"],
        })
        result = await self._structured_llm.ainvoke(prompt_value)
        return result

    async def quick_score(
        self,
        resume_summary: str,
        job_title: str,
        job_company: str,
        job_description: str,
        target_role: str = "Software Engineer",
        experience_level: str = "mid",
    ) -> tuple[int, str]:
        """Fast relevance pre-screening without structured output overhead.

        Args:
            resume_summary: Short summary of candidate's key skills.
            job_title: Job title.
            job_company: Company name.
            job_description: Full job description (will be truncated).
            target_role: The role the user is searching for.
            experience_level: User's experience level.

        Returns:
            Tuple of (relevance score 1-10, short reason string).
        """
        # Truncate description for speed
        job_brief = job_description[:500] if len(job_description) > 500 else job_description

        prompt_value = await QUICK_SCORE_PROMPT.ainvoke({
            "resume_summary": resume_summary,
            "job_title": job_title,
            "job_company": job_company,
            "job_brief": job_brief,
            "target_role": target_role,
            "experience_level": experience_level,
        })

        response = await self._llm.ainvoke(prompt_value)
        text = response.content if hasattr(response, "content") else str(response)

        try:
            data = json.loads(text)
            relevance = int(data.get("relevance", 5))
            reason = str(data.get("reason", ""))
        except (json.JSONDecodeError, ValueError, TypeError):
            logger.warning(f"Failed to parse quick_score response: {text[:100]}")
            relevance = 5
            reason = "Could not parse response"

        return (max(1, min(10, relevance)), reason)
