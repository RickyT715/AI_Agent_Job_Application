"""Cover letter generation using Claude Sonnet.

Uses an LCEL chain: prompt template → Claude at temperature 0.7 → string output.
"""

import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.services.llm_factory import LLMTask, get_llm

logger = logging.getLogger(__name__)

COVER_LETTER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert career coach who writes compelling, personalized cover letters. "
        "Write a professional cover letter that highlights the candidate's strengths relative "
        "to the job requirements. Be genuine and specific — avoid generic filler. "
        "Keep it between 250-500 words.",
    ),
    (
        "human",
        "Write a cover letter for the following job application.\n\n"
        "**Job Title:** {job_title}\n"
        "**Company:** {company}\n"
        "**Job Description:** {job_description}\n\n"
        "**Candidate Resume:**\n{resume_text}\n\n"
        "**Match Strengths:** {strengths}\n"
        "**Areas to Address:** {missing_skills}\n\n"
        "Write a cover letter that emphasizes the strengths and honestly addresses "
        "how the candidate plans to grow in the gap areas.",
    ),
])

COVER_LETTER_TEMPERATURE = 0.7


class CoverLetterGenerator:
    """Generates cover letters using Claude Sonnet."""

    def __init__(self, temperature: float = COVER_LETTER_TEMPERATURE) -> None:
        self._temperature = temperature

    def _build_chain(self):
        """Build the LCEL chain for cover letter generation."""
        llm = get_llm(LLMTask.COVER_LETTER, temperature=self._temperature)
        return COVER_LETTER_PROMPT | llm | StrOutputParser()

    async def generate(
        self,
        job_title: str,
        company: str,
        job_description: str,
        resume_text: str,
        strengths: list[str],
        missing_skills: list[str],
    ) -> str:
        """Generate a cover letter.

        Args:
            job_title: Title of the target job.
            company: Company name.
            job_description: Full job description text.
            resume_text: Candidate's resume text.
            strengths: List of matching strengths.
            missing_skills: List of skill gaps.

        Returns:
            Generated cover letter text.
        """
        chain = self._build_chain()
        result = await chain.ainvoke({
            "job_title": job_title,
            "company": company,
            "job_description": job_description,
            "resume_text": resume_text,
            "strengths": ", ".join(strengths),
            "missing_skills": ", ".join(missing_skills),
        })
        logger.info(f"Generated cover letter: {len(result)} chars")
        return result
