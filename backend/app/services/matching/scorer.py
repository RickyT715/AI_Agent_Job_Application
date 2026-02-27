"""LLM-as-Judge scoring using Claude Sonnet with structured output.

Scores job-resume matches on multiple dimensions using Claude's reasoning.
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from app.schemas.matching import JobMatchScore

SCORING_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert job matching analyst. Score how well a candidate's resume "
        "matches a job posting on multiple dimensions. Be precise and actionable in your "
        "reasoning. Score each dimension from 1 (poor match) to 10 (perfect match).",
    ),
    (
        "human",
        """Evaluate this resume against the job posting.

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

Score each dimension:
- skills (1-10): How well do the candidate's skills match the requirements?
- experience (1-10): Does the experience level and years match?
- education (1-10): Does education background align?
- location (1-10): Is the location compatible with preferences?
- salary (1-10): Does the salary range match expectations?

Also provide:
- overall_score: Weighted average considering all dimensions
- reasoning: 2-3 sentence explanation of the match quality
- strengths: List of matching strengths
- missing_skills: Skills the job requires that the candidate lacks
- interview_talking_points: Key points the candidate should emphasize""",
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
    ) -> JobMatchScore:
        """Score a single job-resume match.

        Returns:
            JobMatchScore with dimension scores, reasoning, and recommendations.
        """
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
        })
        result = await self._structured_llm.ainvoke(prompt_value)
        return result
