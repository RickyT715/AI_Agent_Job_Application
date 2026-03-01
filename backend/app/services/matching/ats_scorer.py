"""ATS (Applicant Tracking System) keyword scorer.

Pure programmatic scorer — zero LLM calls. Computes keyword overlap between
a resume and a job description to estimate ATS pass-through likelihood.

Supports Chinese text via jieba segmentation (auto-detected).
"""

import re

from app.schemas.matching import ATSKeywordScore
from app.services.matching.language_detect import detect_language

# ---------------------------------------------------------------------------
# Curated keyword sets — English
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

# ---------------------------------------------------------------------------
# Curated keyword sets — Chinese
# ---------------------------------------------------------------------------

TECHNICAL_KEYWORDS_ZH: set[str] = {
    # Languages (keep English names that appear in Chinese JDs)
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "sql", "html", "css",
    # Chinese technical terms
    "机器学习", "深度学习", "自然语言处理", "计算机视觉", "人工智能",
    "数据分析", "数据挖掘", "数据库", "大数据", "数据仓库", "数据治理",
    "前端开发", "后端开发", "全栈开发", "移动开发", "客户端开发",
    "微服务", "分布式", "分布式系统", "高并发", "高可用",
    "算法", "数据结构", "设计模式", "系统设计", "架构设计",
    "云计算", "容器化", "虚拟化", "持续集成", "持续部署",
    "测试开发", "自动化测试", "性能测试", "压力测试",
    "运维", "监控", "日志", "告警",
    "网络安全", "信息安全", "渗透测试", "加密",
    "嵌入式", "物联网", "边缘计算",
    "区块链", "智能合约",
    "推荐系统", "搜索引擎", "知识图谱", "语音识别", "图像识别",
    "量化交易", "风控", "反欺诈",
    "操作系统", "编译原理", "计算机网络",
    # Frameworks commonly referenced in Chinese
    "spring boot", "react", "vue", "django", "flask", "fastapi",
    "pytorch", "tensorflow", "kubernetes", "docker",
    "redis", "mysql", "postgresql", "mongodb", "elasticsearch",
    "kafka", "rabbitmq", "nginx", "linux",
    "aws", "azure", "阿里云", "腾讯云", "华为云",
    "git", "jenkins", "ci/cd",
}

SOFT_SKILL_KEYWORDS_ZH: set[str] = {
    "沟通", "沟通能力", "团队合作", "团队协作", "协作能力",
    "领导力", "领导能力", "管理能力",
    "项目管理", "时间管理", "目标管理",
    "问题解决", "分析能力", "逻辑思维", "创新能力",
    "抗压能力", "责任心", "执行力", "主动性",
    "学习能力", "快速学习", "自驱力",
    "跨部门协作", "跨团队沟通",
    "客户导向", "结果导向", "细节导向",
    "演讲", "汇报", "文档能力",
}


# ---------------------------------------------------------------------------
# Tokenizers
# ---------------------------------------------------------------------------

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


def _tokenize_zh(text: str) -> set[str]:
    """Extract tokens from Chinese text using jieba segmentation.

    Also extracts English tokens that appear inline (e.g. ``"Python"``, ``"React"``).
    """
    import jieba  # lazy import to avoid startup cost when not using Chinese

    tokens: set[str] = set()
    words = list(jieba.cut(text))
    for w in words:
        w = w.strip()
        if w:
            tokens.add(w.lower())

    # Bigrams for multi-character Chinese phrases jieba may split
    for i in range(len(words) - 1):
        a = words[i].strip()
        b = words[i + 1].strip()
        if a and b:
            tokens.add(f"{a}{b}".lower())

    # Also run the English tokenizer on extracted Latin substrings
    latin_text = " ".join(re.findall(r"[a-zA-Z0-9.#+]+", text))
    if latin_text:
        tokens.update(_tokenize(latin_text))

    return tokens


# ---------------------------------------------------------------------------
# Keyword extraction
# ---------------------------------------------------------------------------

def _extract_keywords(text: str) -> tuple[set[str], set[str]]:
    """Extract technical and soft-skill keywords found in text (English).

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


def _extract_keywords_zh(text: str) -> tuple[set[str], set[str]]:
    """Extract technical and soft-skill keywords from Chinese text.

    Returns:
        (technical_keywords_found, soft_skill_keywords_found)
    """
    tokens = _tokenize_zh(text)

    technical = set()
    for kw in TECHNICAL_KEYWORDS_ZH:
        if kw.lower() in tokens:
            technical.add(kw)

    soft = set()
    for kw in SOFT_SKILL_KEYWORDS_ZH:
        if kw.lower() in tokens:
            soft.add(kw)

    return technical, soft


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------

def compute_ats_score(
    resume_text: str,
    job_description: str,
    job_requirements: str | None = None,
    ats_mode: str = "auto",
) -> ATSKeywordScore | None:
    """Compute ATS keyword overlap score between resume and job posting.

    Algorithm:
    - Extract keywords from job description + requirements
    - Check which appear in resume
    - Weighted score: 70% technical + 30% soft skills

    Args:
        resume_text: Full resume text.
        job_description: Job description text.
        job_requirements: Optional separate requirements text.
        ats_mode: Scoring mode — ``"auto"`` (jieba for Chinese, regex for English),
                  ``"skip"`` (return None), or ``"llm"`` (not handled here).

    Returns:
        ATSKeywordScore with overlap metrics, or None if mode is ``"skip"``.
    """
    if ats_mode == "skip":
        return None

    # Combine job text
    job_text = job_description
    if job_requirements:
        job_text = f"{job_text}\n{job_requirements}"

    # Detect language and pick extraction strategy
    lang = detect_language(job_text)
    if ats_mode == "auto" and lang == "zh":
        extract_fn = _extract_keywords_zh
    else:
        extract_fn = _extract_keywords

    # Extract keywords from job posting
    job_technical, job_soft = extract_fn(job_text)
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

    # Extract keywords from resume (use same extraction strategy)
    resume_technical, resume_soft = extract_fn(resume_text)

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


async def compute_ats_score_llm(
    resume_text: str,
    job_description: str,
    llm,
    job_requirements: str | None = None,
) -> ATSKeywordScore:
    """Compute ATS score using an LLM to extract keywords (more accurate, costs ~1 call).

    Args:
        resume_text: Full resume text.
        job_description: Job description text.
        llm: A LangChain chat model instance.
        job_requirements: Optional separate requirements text.

    Returns:
        ATSKeywordScore with LLM-extracted keyword overlap metrics.
    """
    import json as _json

    job_text = job_description
    if job_requirements:
        job_text = f"{job_text}\n{job_requirements}"

    prompt = (
        "Extract all technical skills, tools, frameworks, programming languages, "
        "and soft skills mentioned in the following text. "
        'Return valid JSON with keys: "technical" (list of strings), '
        '"soft" (list of strings).\n\n'
        "Text:\n{text}\n\nJSON:"
    )

    # Extract from job text
    job_response = await llm.ainvoke(prompt.format(text=job_text[:3000]))
    job_content = (
        job_response.content
        if hasattr(job_response, "content")
        else str(job_response)
    )
    try:
        job_kws = _json.loads(job_content)
    except _json.JSONDecodeError:
        # Try to extract JSON from response
        match = re.search(r"\{.*\}", job_content, re.DOTALL)
        job_kws = _json.loads(match.group()) if match else {"technical": [], "soft": []}

    # Extract from resume
    resume_response = await llm.ainvoke(prompt.format(text=resume_text[:3000]))
    resume_content = (
        resume_response.content
        if hasattr(resume_response, "content")
        else str(resume_response)
    )
    try:
        resume_kws = _json.loads(resume_content)
    except _json.JSONDecodeError:
        match = re.search(r"\{.*\}", resume_content, re.DOTALL)
        resume_kws = _json.loads(match.group()) if match else {"technical": [], "soft": []}

    # Normalize and compute overlap
    job_tech = {k.lower().strip() for k in job_kws.get("technical", [])}
    job_soft = {k.lower().strip() for k in job_kws.get("soft", [])}
    res_tech = {k.lower().strip() for k in resume_kws.get("technical", [])}
    res_soft = {k.lower().strip() for k in resume_kws.get("soft", [])}

    matched_tech = job_tech & res_tech
    matched_soft = job_soft & res_soft
    all_job = job_tech | job_soft
    matched = matched_tech | matched_soft
    missing = all_job - matched

    tech_pct = (len(matched_tech) / len(job_tech) * 100.0) if job_tech else 100.0
    soft_pct = (len(matched_soft) / len(job_soft) * 100.0) if job_soft else 100.0
    score = tech_pct * 0.70 + soft_pct * 0.30

    return ATSKeywordScore(
        score=round(min(score, 100.0), 1),
        matched_keywords=sorted(matched),
        missing_keywords=sorted(missing),
        total_job_keywords=len(all_job),
        technical_match_pct=round(tech_pct, 1),
        soft_skill_match_pct=round(soft_pct, 1),
    )
