"""Real user simulation using Gemini 3.1 API with actual user data.

Tests the full pipeline:
1. Parse resume with Gemini 3.1
2. Generate embeddings with gemini-embedding-001
3. Index jobs into ChromaDB
4. Retrieve + rerank candidates
5. Score matches (Gemini 3.1 as fallback since no Claude key)
6. Generate cover letter (Gemini 3.1)
7. Generate HTML report

Usage:
    cd backend
    uv run python scripts/real_user_test.py
"""

import asyncio
import logging
import os
import sys
import tempfile

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Load .env from project root (parent of backend/)
from dotenv import load_dotenv
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("real_user_test")

# ---------------------------------------------------------------------------
# User resume from User_information_prompts.txt
# ---------------------------------------------------------------------------
RESUME_TEXT = """
Ruiqi Tian
Email: ruiqitian@outlook.com | Mobile: +1-236-989-3086
LinkedIn: https://www.linkedin.com/in/ruiqi-tian-a53159249/
GitHub: https://github.com/RickyT715

EDUCATION
- Master of Engineering in Electrical and Computer Engineering, GPA: 3.9
  University of Waterloo, Waterloo, ON (Sept 2024 - Oct 2025)
  Specialization: Software Engineering, Full-stack Development, Computer Graphics,
  Computer Vision, Reinforcement Learning, LLM, DevOps, Performance Test, Autonomous Driving

- Bachelor of Applied Science in Computer Engineering, GPA: 3.7
  University of British Columbia, Vancouver, BC (Sept 2020 - May 2024)
  Specialization: Software Engineering, Full-stack Development, Phone App Development,
  Computer Graphics, Computer Vision, Deep Learning, Embedded Development, Operating System
  Honor: 2022, 2023, 2024 Dean's Honor List

EXPERIENCE
Software Engineer Intern | Disanji Technology Institute (Jun 2024 - Aug 2024)
- Architected end-to-end RAG pipeline (LangChain LCEL) for online QA platform over 500+ pages
  Chinese documents with modular retrieval, re-ranking, and streaming generation
- Implemented hybrid search (BM25 + BGE-M3 dense/sparse vectors, RRF fusion) with cross-encoder
  re-ranking (top-30 -> top-5), improving precision 35% over vector-only baseline
- Built RAGAS evaluation pipeline with 100-question golden dataset + GitHub Actions CI;
  achieved 0.84 context recall, 0.82 faithfulness, reducing hallucinations 15% -> 4%
- Deployed via Docker Compose with FastAPI + SSE streaming, Redis semantic caching (60% fewer
  API calls), and Langfuse tracing. P95 latency <2s

Research Assistant | Nanjing University (Jun 2023 - Aug 2023)
- Co-developed DBVM, a dual-branch pipeline combining knowledge graphs and video-language models
  for multimodal QA on 90-min movies
- Designed cross-matching strategy fusing T2V/V2T similarity matrices, improving accuracy 0.52 to 0.76
- Published "Deep Video Understanding with Video-Language Model" in ACM MM '23 proceedings

Software Engineer Intern | GuoLing Technology Institute (Apr 2023 - May 2023)
- Trained 4 face-specific YOLOv8 models for industrial defect detection across 20 classes,
  achieving 91% mAP@50
- Built end-to-end data pipeline processing 5,000+ images from 7 cameras

PROJECTS
AI Agent-powered Resume & Cover Letter Generator (Oct 2025 - Feb 2026)
- Architected a 4-agent LangGraph pipeline with quality-gated routing and retry loops
- Engineered a RAG pipeline using ChromaDB and BGE-M3 embeddings over scraped company data
- Built dual-layer evaluation with ATS keyword scoring (spaCy/TF-IDF) and LLM-as-a-judge
- Deployed full-stack app with FastAPI, React/TypeScript, WebSocket streaming, PostgreSQL,
  Docker, and 80%+ test coverage via CI/CD

Aerial Drone Footage – Lost Hiker Challenge (Sep 2023 - Apr 2024)
- Developed YOLOv8 model for detecting lost hikers in aerial drone footage
- Implemented SAHI pipeline with OpenCV to process 4K video for small object detection

SKILLS
Languages: Python, JavaScript, C++, SQL, Java, Verilog, VHDL, HTML, CSS, Lua
Technologies: AWS, Azure, Kafka, React, Vue, Qt, Git, Android Studio
AI/ML: RAG, LLM, LangChain, LangGraph, ChromaDB, Computer Vision, YOLOv8, Deep Learning
"""

# ---------------------------------------------------------------------------
# Realistic job postings (mix of good and poor matches)
# ---------------------------------------------------------------------------
SAMPLE_JOBS = [
    {
        "external_id": "job-001",
        "source": "greenhouse",
        "title": "AI/ML Engineer",
        "company": "Scale AI",
        "location": "San Francisco, CA (Remote)",
        "workplace_type": "remote",
        "description": "Build and deploy ML models for data labeling and AI training pipelines. "
        "Work on LLM fine-tuning, RAG systems, and evaluation frameworks.",
        "requirements": "3+ years ML engineering, Python, PyTorch/TensorFlow, RAG pipelines, "
        "LangChain, vector databases, CI/CD. MS in CS/ML preferred.",
        "salary_min": 150000,
        "salary_max": 220000,
        "salary_currency": "USD",
        "employment_type": "full-time",
        "experience_level": "mid",
    },
    {
        "external_id": "job-002",
        "source": "lever",
        "title": "Full Stack Software Engineer",
        "company": "Shopify",
        "location": "Toronto, ON (Remote)",
        "workplace_type": "remote",
        "description": "Build scalable e-commerce features using React, TypeScript, and Ruby on Rails. "
        "Work on checkout flows, merchant dashboards, and API integrations.",
        "requirements": "2+ years full-stack, React/TypeScript, REST APIs, PostgreSQL, "
        "Docker, CI/CD, cloud platforms (AWS/GCP).",
        "salary_min": 120000,
        "salary_max": 180000,
        "salary_currency": "CAD",
        "employment_type": "full-time",
        "experience_level": "mid",
    },
    {
        "external_id": "job-003",
        "source": "jsearch",
        "title": "Backend Engineer - LLM Platform",
        "company": "Cohere",
        "location": "Toronto, ON",
        "workplace_type": "hybrid",
        "description": "Design and scale the backend infrastructure for LLM serving and fine-tuning. "
        "Build APIs for model inference, RAG pipelines, and embedding services.",
        "requirements": "Python, FastAPI/Flask, distributed systems, Docker/Kubernetes, "
        "LLM deployment, vector databases (ChromaDB/Pinecone), Redis.",
        "salary_min": 140000,
        "salary_max": 200000,
        "salary_currency": "CAD",
        "employment_type": "full-time",
        "experience_level": "mid",
    },
    {
        "external_id": "job-004",
        "source": "jsearch",
        "title": "Computer Vision Engineer",
        "company": "Waymo",
        "location": "Mountain View, CA",
        "workplace_type": "onsite",
        "description": "Develop perception algorithms for autonomous vehicles. Work on object detection, "
        "tracking, and 3D scene understanding using camera and LiDAR data.",
        "requirements": "MS/PhD in CS or EE, Python, C++, PyTorch, computer vision, "
        "object detection (YOLO family), 3D point cloud processing.",
        "salary_min": 160000,
        "salary_max": 250000,
        "salary_currency": "USD",
        "employment_type": "full-time",
        "experience_level": "mid",
    },
    {
        "external_id": "job-005",
        "source": "greenhouse",
        "title": "Senior Accountant",
        "company": "Deloitte",
        "location": "Toronto, ON",
        "workplace_type": "hybrid",
        "description": "Manage financial audits and prepare tax returns for enterprise clients. "
        "Lead a team of junior accountants.",
        "requirements": "CPA designation, 5+ years audit experience, IFRS, GAAP, Excel.",
        "salary_min": 85000,
        "salary_max": 120000,
        "salary_currency": "CAD",
        "employment_type": "full-time",
        "experience_level": "senior",
    },
    {
        "external_id": "job-006",
        "source": "lever",
        "title": "DevOps Engineer",
        "company": "Datadog",
        "location": "New York, NY (Remote)",
        "workplace_type": "remote",
        "description": "Build and maintain CI/CD pipelines, Kubernetes clusters, and monitoring "
        "infrastructure. Automate deployment workflows for cloud-native services.",
        "requirements": "3+ years DevOps, Docker, Kubernetes, Terraform, AWS/GCP, "
        "Python/Go scripting, GitHub Actions, monitoring (Prometheus/Grafana).",
        "salary_min": 140000,
        "salary_max": 200000,
        "salary_currency": "USD",
        "employment_type": "full-time",
        "experience_level": "mid",
    },
    {
        "external_id": "job-007",
        "source": "jsearch",
        "title": "Machine Learning Engineer - NLP",
        "company": "Hugging Face",
        "location": "Remote",
        "workplace_type": "remote",
        "description": "Develop and optimize transformer models, fine-tuning pipelines, and inference "
        "infrastructure. Contribute to open-source ML libraries and Hub features.",
        "requirements": "Python, PyTorch, transformers, NLP, LLM fine-tuning, "
        "distributed training, Docker, Git. MS/PhD preferred.",
        "salary_min": 160000,
        "salary_max": 230000,
        "salary_currency": "USD",
        "employment_type": "full-time",
        "experience_level": "mid",
    },
    {
        "external_id": "job-008",
        "source": "greenhouse",
        "title": "Registered Nurse",
        "company": "Toronto General Hospital",
        "location": "Toronto, ON",
        "workplace_type": "onsite",
        "description": "Provide direct patient care in the emergency department.",
        "requirements": "BScN, CNO registration, BCLS certification, 2+ years ER experience.",
        "salary_min": 70000,
        "salary_max": 95000,
        "salary_currency": "CAD",
        "employment_type": "full-time",
        "experience_level": "mid",
    },
]

# ---------------------------------------------------------------------------
# User preferences
# ---------------------------------------------------------------------------
USER_PREFERENCES = {
    "job_titles": ["Software Engineer", "ML Engineer", "AI Engineer", "Backend Engineer"],
    "locations": ["Remote", "Toronto, ON", "Waterloo, ON", "Vancouver, BC"],
    "salary_min": 100000,
    "salary_max": 250000,
    "workplace_types": ["remote", "hybrid"],
    "experience_level": "mid",
}


async def main():
    """Run the full real-user simulation."""
    from app.config import Settings, UserConfig, get_settings, reset_settings
    from app.schemas.matching import JobMatchScore, JobPosting, ScoreBreakdown, ScoredMatch
    from app.services.llm_factory import get_embeddings, get_llm, LLMTask
    from app.services.matching.embedder import JobEmbedder
    from app.services.matching.retriever import TwoStageRetriever
    from app.services.reports.generator import ReportGenerator

    reset_settings()
    settings = get_settings()

    print("=" * 70)
    print("  AI Job Application Agent - Real User Simulation")
    print("=" * 70)
    print()
    print(f"  Gemini Model:    {settings.gemini_model}")
    print(f"  Embedding Model: {settings.embedding_model}")
    print(f"  Claude Model:    {settings.claude_model}")
    print(f"  Google API Key:  {'***' + settings.google_api_key.get_secret_value()[-4:]}")
    print()

    # ------------------------------------------------------------------
    # Step 1: Parse resume with Gemini 3.1
    # ------------------------------------------------------------------
    print("-" * 70)
    print("  STEP 1: Parse Resume with Gemini 3.1")
    print("-" * 70)

    llm = get_llm(LLMTask.PARSE)
    parse_prompt = (
        "Extract structured information from this resume. Return a JSON object with: "
        "name, email, phone, education (list), experience (list with title, company, dates), "
        "skills (list), projects (list).\n\n"
        f"{RESUME_TEXT}"
    )

    try:
        result = await llm.ainvoke(parse_prompt)
        print(f"  [OK] Resume parsed successfully ({len(result.content)} chars)")
        print(f"  Preview: {result.content[:200]}...")
        print()
    except Exception as e:
        print(f"  [ERROR] Resume parsing failed: {e}")
        print()
        raise

    # ------------------------------------------------------------------
    # Step 2: Extract keywords with Gemini 3.1
    # ------------------------------------------------------------------
    print("-" * 70)
    print("  STEP 2: Extract Keywords with Gemini 3.1")
    print("-" * 70)

    extract_llm = get_llm(LLMTask.EXTRACT)
    extract_prompt = (
        "Extract the top 20 technical skills and keywords from this resume. "
        "Return as a comma-separated list.\n\n"
        f"{RESUME_TEXT}"
    )

    try:
        result = await extract_llm.ainvoke(extract_prompt)
        print(f"  [OK] Keywords extracted: {result.content[:300]}")
        print()
    except Exception as e:
        print(f"  [ERROR] Keyword extraction failed: {e}")
        print()
        raise

    # ------------------------------------------------------------------
    # Step 3: Generate embeddings and index jobs
    # ------------------------------------------------------------------
    print("-" * 70)
    print("  STEP 3: Generate Embeddings & Index Jobs (gemini-embedding-001)")
    print("-" * 70)

    # Use ephemeral ChromaDB for testing
    import chromadb
    chroma_client = chromadb.EphemeralClient()

    embeddings = get_embeddings("retrieval_document")
    embedder = JobEmbedder(embeddings=embeddings, chroma_client=chroma_client)

    jobs = [JobPosting(**j) for j in SAMPLE_JOBS]

    try:
        new_count = embedder.index_jobs(jobs)
        total = embedder.get_collection_count()
        print(f"  [OK] Indexed {new_count} jobs (total in store: {total})")
        print()
    except Exception as e:
        print(f"  [ERROR] Indexing failed: {e}")
        print()
        raise

    # ------------------------------------------------------------------
    # Step 4: Retrieve + Rerank candidates
    # ------------------------------------------------------------------
    print("-" * 70)
    print("  STEP 4: Retrieve & Rerank Candidates")
    print("-" * 70)

    try:
        retriever = TwoStageRetriever(
            vectorstore=embedder.vectorstore,
            initial_k=min(8, total),  # We only have 8 jobs
            final_k=min(5, total),
        )
        retrieved_docs = retriever.retrieve(RESUME_TEXT)
        print(f"  [OK] Retrieved {len(retrieved_docs)} candidates after reranking")
        for i, doc in enumerate(retrieved_docs):
            title = doc.metadata.get("title", "?")
            company = doc.metadata.get("company", "?")
            print(f"    {i+1}. {title} @ {company}")
        print()
    except Exception as e:
        print(f"  [ERROR] Retrieval failed: {e}")
        print()
        raise

    # ------------------------------------------------------------------
    # Step 5: Score matches with Gemini 3.1 (substitute for Claude)
    # ------------------------------------------------------------------
    print("-" * 70)
    print("  STEP 5: Score Matches with Gemini 3.1 (LLM-as-Judge)")
    print("-" * 70)
    print("  Note: Using Gemini 3.1 instead of Claude (no Anthropic key)")
    print()

    # Use Gemini 3.1 as scorer instead of Claude
    scorer_llm = get_llm(LLMTask.PARSE, temperature=0.0)  # Reuse Gemini
    from app.services.matching.scorer import JobScorer
    scorer = JobScorer(llm=scorer_llm)

    user_config = UserConfig(**USER_PREFERENCES)
    preferred_locations = ", ".join(user_config.locations)
    salary_range = f"${user_config.salary_min:,} - ${user_config.salary_max:,}"

    scored_matches: list[ScoredMatch] = []
    jobs_by_key = {f"{j.source}:{j.external_id}": j for j in jobs}

    for i, doc in enumerate(retrieved_docs):
        job_key = f"{doc.metadata.get('source', '')}:{doc.metadata.get('job_id', '')}"
        job = jobs_by_key.get(job_key)
        if not job:
            # Reconstruct from metadata
            job = JobPosting(
                external_id=doc.metadata.get("job_id", "unknown"),
                source=doc.metadata.get("source", "unknown"),
                title=doc.metadata.get("title", "Unknown"),
                company=doc.metadata.get("company", "Unknown"),
                location=doc.metadata.get("location") or None,
                description=doc.page_content,
            )

        try:
            score = await scorer.score(
                resume_text=RESUME_TEXT,
                job_title=job.title,
                job_company=job.company,
                job_description=job.description,
                job_location=job.location or "Not specified",
                job_requirements=job.requirements or "Not specified",
                job_salary=(
                    f"${job.salary_min:,} - ${job.salary_max:,}"
                    if job.salary_min and job.salary_max
                    else "Not specified"
                ),
                preferred_locations=preferred_locations,
                salary_range=salary_range,
            )
            scored_matches.append(ScoredMatch(job=job, score=score))
            print(f"  [{i+1}/{len(retrieved_docs)}] {job.title} @ {job.company}")
            print(f"    Overall: {score.overall_score:.1f}/10")
            print(f"    Skills: {score.breakdown.skills}, Exp: {score.breakdown.experience}, "
                  f"Edu: {score.breakdown.education}, Loc: {score.breakdown.location}, "
                  f"Sal: {score.breakdown.salary}")
            print(f"    Strengths: {', '.join(score.strengths[:3])}")
            if score.missing_skills:
                print(f"    Gaps: {', '.join(score.missing_skills[:3])}")
            print()
        except Exception as e:
            print(f"  [ERROR] Scoring {job.title} failed: {e}")
            print()

    # Sort by score
    scored_matches.sort(key=lambda m: m.score.overall_score, reverse=True)

    print("-" * 70)
    print("  RESULTS: Ranked Matches")
    print("-" * 70)
    for i, match in enumerate(scored_matches):
        emoji = "***" if match.score.overall_score >= 8 else "**" if match.score.overall_score >= 6 else "*"
        print(f"  {i+1}. [{match.score.overall_score:.1f}] {emoji} {match.job.title} @ {match.job.company}")
        print(f"     {match.score.reasoning[:120]}")
    print()

    # ------------------------------------------------------------------
    # Step 6: Generate cover letter with Gemini 3.1 (substitute for Claude)
    # ------------------------------------------------------------------
    if scored_matches:
        print("-" * 70)
        print("  STEP 6: Generate Cover Letter (Gemini 3.1)")
        print("-" * 70)

        top_match = scored_matches[0]

        # Use Gemini directly for cover letter (since no Claude key)
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate

        cl_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are an expert career coach. Write a professional cover letter (250-500 words) "
             "for the candidate. Be genuine, specific, and highlight strengths."),
            ("human",
             "Write a cover letter for:\n\n"
             "**Job:** {job_title} at {company}\n"
             "**Description:** {job_description}\n\n"
             "**Resume:**\n{resume_text}\n\n"
             "**Strengths:** {strengths}\n"
             "**Gaps to address:** {missing_skills}"),
        ])

        cl_chain = cl_prompt | get_llm(LLMTask.PARSE, temperature=0.7) | StrOutputParser()

        try:
            cover_letter = await cl_chain.ainvoke({
                "job_title": top_match.job.title,
                "company": top_match.job.company,
                "job_description": top_match.job.description,
                "resume_text": RESUME_TEXT,
                "strengths": ", ".join(top_match.score.strengths),
                "missing_skills": ", ".join(top_match.score.missing_skills),
            })
            print(f"  [OK] Cover letter generated ({len(cover_letter)} chars)")
            print()
            print(cover_letter[:500])
            print("  ...")
            print()
        except Exception as e:
            print(f"  [ERROR] Cover letter generation failed: {e}")
            cover_letter = None
            print()

        # ------------------------------------------------------------------
        # Step 7: Generate HTML Report
        # ------------------------------------------------------------------
        print("-" * 70)
        print("  STEP 7: Generate Report")
        print("-" * 70)

        try:
            generator = ReportGenerator()
            html = generator.render_html(
                job_title=top_match.job.title,
                company=top_match.job.company,
                overall_score=top_match.score.overall_score,
                breakdown={
                    "Skills": top_match.score.breakdown.skills,
                    "Experience": top_match.score.breakdown.experience,
                    "Education": top_match.score.breakdown.education,
                    "Location": top_match.score.breakdown.location,
                    "Salary": top_match.score.breakdown.salary,
                },
                reasoning=top_match.score.reasoning,
                strengths=top_match.score.strengths,
                missing_skills=top_match.score.missing_skills,
                interview_talking_points=top_match.score.interview_talking_points,
                salary_min=top_match.job.salary_min,
                salary_max=top_match.job.salary_max,
                salary_currency=top_match.job.salary_currency,
                cover_letter=cover_letter,
            )
            # Save to temp file
            report_path = os.path.join(tempfile.gettempdir(), "job_match_report.html")
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  [OK] HTML report saved to: {report_path}")
            print(f"  Report size: {len(html)} chars")
            print()
        except Exception as e:
            print(f"  [ERROR] Report generation failed: {e}")
            print()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("=" * 70)
    print("  SIMULATION COMPLETE")
    print("=" * 70)
    print(f"  Jobs indexed:    {len(jobs)}")
    print(f"  Jobs retrieved:  {len(retrieved_docs)}")
    print(f"  Jobs scored:     {len(scored_matches)}")
    if scored_matches:
        print(f"  Top match:       {scored_matches[0].job.title} @ {scored_matches[0].job.company}")
        print(f"  Top score:       {scored_matches[0].score.overall_score:.1f}/10")
    print()


if __name__ == "__main__":
    asyncio.run(main())
