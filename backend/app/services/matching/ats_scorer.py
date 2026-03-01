"""ATS (Applicant Tracking System) keyword scorer.

Pure programmatic scorer — zero LLM calls. Computes keyword overlap between
a resume and a job description to estimate ATS pass-through likelihood.
"""

import re

from app.schemas.matching import ATSKeywordScore

# ---------------------------------------------------------------------------
# Curated keyword sets
# ---------------------------------------------------------------------------

TECHNICAL_KEYWORDS: set[str] = {
    # Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "sql", "html",
    "css", "bash", "shell", "perl", "lua", "dart", "elixir", "haskell",
    "objective-c", "matlab", "julia",
    # Frameworks & Libraries
    "react", "angular", "vue", "vue.js", "next.js", "nextjs", "nuxt",
    "svelte", "django", "flask", "fastapi", "express", "express.js",
    "spring", "spring boot", "rails", "ruby on rails", "laravel", "asp.net",
    ".net", "node.js", "nodejs", "nestjs", "gin", "fiber",
    # AI/ML
    "machine learning", "deep learning", "natural language processing", "nlp",
    "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn",
    "sklearn", "pandas", "numpy", "langchain", "llm", "large language model",
    "rag", "retrieval augmented generation", "transformers", "hugging face",
    "openai", "gpt", "bert", "fine-tuning", "prompt engineering",
    # Data
    "sql", "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "sqlite", "oracle", "snowflake", "bigquery",
    "apache spark", "spark", "hadoop", "kafka", "airflow", "dbt",
    "data pipeline", "etl", "data warehouse", "data lake",
    # Cloud & Infrastructure
    "aws", "amazon web services", "azure", "gcp", "google cloud",
    "docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins",
    "github actions", "gitlab ci", "ci/cd", "cicd", "linux", "nginx",
    "cloudformation", "serverless", "lambda", "ecs", "eks", "fargate",
    # Tools & Practices
    "git", "github", "gitlab", "bitbucket", "jira", "confluence",
    "agile", "scrum", "kanban", "tdd", "test driven development",
    "microservices", "rest", "restful", "graphql", "grpc", "api",
    "oauth", "jwt", "websocket", "rabbitmq", "celery",
    # Security
    "cybersecurity", "penetration testing", "owasp", "encryption", "ssl", "tls",
    "soc 2", "gdpr", "hipaa", "iam",
    # Mobile
    "ios", "android", "react native", "flutter", "xamarin", "swiftui",
    # DevOps/SRE
    "devops", "sre", "site reliability", "monitoring", "prometheus",
    "grafana", "datadog", "new relic", "splunk", "observability",
    "load balancing", "auto scaling",
}

SOFT_SKILL_KEYWORDS: set[str] = {
    "leadership", "communication", "teamwork", "collaboration",
    "problem solving", "problem-solving", "critical thinking",
    "time management", "project management", "mentoring", "coaching",
    "presentation", "stakeholder management", "cross-functional",
    "self-motivated", "detail-oriented", "analytical",
    "adaptability", "creativity", "initiative", "negotiation",
    "conflict resolution", "decision making", "decision-making",
    "strategic thinking", "customer-focused", "results-driven",
    "interpersonal", "organizational",
}


def _tokenize(text: str) -> set[str]:
    """Extract normalized unigrams, bigrams, and trigrams from text."""
    text_lower = text.lower()
    # Replace common separators with spaces
    text_clean = re.sub(r"[/,;|•·\-–—]", " ", text_lower)
    # Keep alphanumeric, dots (for .net, node.js), hashes (c#), pluses (c++)
    text_clean = re.sub(r"[^a-z0-9.#+\s]", " ", text_clean)
    words = text_clean.split()

    tokens: set[str] = set()
    for w in words:
        w_stripped = w.strip(".")
        if w_stripped:
            tokens.add(w_stripped)

    # Bigrams
    for i in range(len(words) - 1):
        bigram = f"{words[i].strip('.')} {words[i+1].strip('.')}".strip()
        if bigram:
            tokens.add(bigram)

    # Trigrams
    for i in range(len(words) - 2):
        trigram = (
            f"{words[i].strip('.')} {words[i+1].strip('.')} "
            f"{words[i+2].strip('.')}".strip()
        )
        if trigram:
            tokens.add(trigram)

    return tokens


def _extract_keywords(text: str) -> tuple[set[str], set[str]]:
    """Extract technical and soft-skill keywords found in text.

    Returns:
        (technical_keywords_found, soft_skill_keywords_found)
    """
    tokens = _tokenize(text)

    technical = set()
    for kw in TECHNICAL_KEYWORDS:
        if kw in tokens:
            technical.add(kw)

    soft = set()
    for kw in SOFT_SKILL_KEYWORDS:
        if kw in tokens:
            soft.add(kw)

    return technical, soft


def compute_ats_score(
    resume_text: str,
    job_description: str,
    job_requirements: str | None = None,
) -> ATSKeywordScore:
    """Compute ATS keyword overlap score between resume and job posting.

    Algorithm:
    - Extract keywords from job description + requirements
    - Check which appear in resume
    - Weighted score: 70% technical + 30% soft skills

    Args:
        resume_text: Full resume text.
        job_description: Job description text.
        job_requirements: Optional separate requirements text.

    Returns:
        ATSKeywordScore with overlap metrics.
    """
    # Combine job text
    job_text = job_description
    if job_requirements:
        job_text = f"{job_text}\n{job_requirements}"

    # Extract keywords from job posting
    job_technical, job_soft = _extract_keywords(job_text)
    all_job_keywords = job_technical | job_soft

    if not all_job_keywords:
        return ATSKeywordScore(
            score=0.0,
            matched_keywords=[],
            missing_keywords=[],
            total_job_keywords=0,
            technical_match_pct=0.0,
            soft_skill_match_pct=0.0,
        )

    # Extract keywords from resume
    resume_technical, resume_soft = _extract_keywords(resume_text)

    # Compute overlap
    matched_technical = job_technical & resume_technical
    matched_soft = job_soft & resume_soft
    matched = matched_technical | matched_soft
    missing = all_job_keywords - matched

    # Percentages
    tech_pct = (
        (len(matched_technical) / len(job_technical) * 100.0)
        if job_technical
        else 100.0
    )
    soft_pct = (
        (len(matched_soft) / len(job_soft) * 100.0)
        if job_soft
        else 100.0
    )

    # Weighted score: 70% technical, 30% soft skills
    score = tech_pct * 0.70 + soft_pct * 0.30

    return ATSKeywordScore(
        score=round(min(score, 100.0), 1),
        matched_keywords=sorted(matched),
        missing_keywords=sorted(missing),
        total_job_keywords=len(all_job_keywords),
        technical_match_pct=round(tech_pct, 1),
        soft_skill_match_pct=round(soft_pct, 1),
    )
