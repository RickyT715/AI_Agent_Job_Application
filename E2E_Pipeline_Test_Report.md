# AI Job Application Agent — End-to-End Pipeline Test Report

**Generated:** 2026-02-27 21:53 UTC
**User:** Ruiqi Tian (Master of Engineering, U of Waterloo)
**Search Titles:** Software Engineer, AI Engineer, Full-stack Developer
**Target Locations:** Remote, United States, Canada
**Salary Range:** $100,000 - $200,000 USD
**Workplace:** remote, hybrid

---
## Executive Summary

| Metric | Value |
|--------|-------|
| Total Jobs Scraped | 166 |
| Total Jobs Scored | 60 |
| Search Queries | 3 |
| Scraping Sources | arbeitnow, greenhouse |
| Scoring Model | Gemini (via Google AI) |
| Embedding Model | Gemini embedding-001 |
| Retrieval | ChromaDB (top-30) → FlashRank rerank (top-20) |

### Per-Title Summary

| Search Query | Scraped | Scored | Avg Score | Top Score | Duration |
|-------------|---------|--------|-----------|-----------|----------|
| Software Engineer | 100 | 20 | 4.4/10 | 6.8/10 | 448.9s |
| AI Engineer | 32 | 20 | 4.7/10 | 7.4/10 | 426.9s |
| Full-stack Developer | 34 | 20 | 4.1/10 | 8.0/10 | 432.9s |

---
## Scraping Sources & Methodology

| Source | Type | Auth Required | Method |
|--------|------|---------------|--------|
| Arbeitnow | Public API | No | Full-text search with keyword filtering across 5 pages |
| Greenhouse | Public Board API | No | Fetched ALL jobs from company boards, filtered by title keywords |
| Lever | Public Postings API | No | Fetched ALL postings from companies, filtered by title keywords |

**Matching Pipeline:**
1. **Scraping** → Collect raw jobs from all enabled sources
2. **Deduplication** → Remove duplicate postings (URL + title matching)
3. **Embedding** → Gemini embedding-001 encodes job descriptions into vectors
4. **Vector Search** → ChromaDB retrieves top-30 most similar to user's resume
5. **Reranking** → FlashRank cross-encoder reranks to top-20
6. **LLM Scoring** → Gemini LLM-as-Judge produces structured score (0-10) with breakdown

---
## Top 10 Matches Across All Searches

| # | Score | Company | Title | Location | Search Query | Apply Link |
|---|-------|---------|-------|----------|-------------|------------|
| 1 | 8.0/10 | Figma | Software Engineer, Full Stack | San Francisco, CA • New York, NY • United States | Full-stack Developer | [Apply](https://boards.greenhouse.io/figma/jobs/5691911004?gh_jid=5691911004) |
| 2 | 7.4/10 | Cloudflare | Software Engineer Intern (Summer 2026) - Austin, TX | In-Office | AI Engineer | N/A |
| 3 | 6.8/10 | Figma | Software Engineer Intern, Developer Tools (2026) (London, United Kingdom) | London, England | Software Engineer | [Apply](https://boards.greenhouse.io/figma/jobs/5621177004?gh_jid=5621177004) |
| 4 | 6.8/10 | Figma | Software Engineer Intern, Developer Tools (2026) (London, United Kingdom) | London, England | AI Engineer | N/A |
| 5 | 6.5/10 | Cloudflare | Software Engineer Intern (Summer 2026) - Austin, TX | In-Office | Software Engineer | [Apply](https://boards.greenhouse.io/cloudflare/jobs/7206269?gh_jid=7206269) |
| 6 | 6.4/10 | Cloudflare | Fullstack Software Engineer | Hybrid | Full-stack Developer | [Apply](https://boards.greenhouse.io/cloudflare/jobs/7542471?gh_jid=7542471) |
| 7 | 6.2/10 | Cloudflare | Software Engineer, AI - Lisbon | Hybrid | Software Engineer | [Apply](https://boards.greenhouse.io/cloudflare/jobs/6998511?gh_jid=6998511) |
| 8 | 6.2/10 | Cloudflare | Software Engineer - Network Services | Hybrid | Software Engineer | [Apply](https://boards.greenhouse.io/cloudflare/jobs/7343760?gh_jid=7343760) |
| 9 | 6.0/10 | Databricks | AI Engineer - FDE (Forward Deployed Engineer) | Melbourne, Australia | AI Engineer | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8330188002) |
| 10 | 6.0/10 | Databricks | AI Engineer - FDE (Forward Deployed Engineer) | Sydney, Australia | AI Engineer | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8298792002) |

---
## Search: "Software Engineer"

**Jobs Scraped:** 100 unique
**Jobs Scored:** 20
**Sources:** greenhouse, arbeitnow
**Duration:** 448.9s

**Average Score:** 4.4/10

### Match Results Overview

| # | Score | Company | Title | Location | Source | Apply Link |
|---|-------|---------|-------|----------|--------|------------|
| 1 | 6.8/10 | Figma | Software Engineer Intern, Developer Tools (2026) (London, United Kingdom) | London, England | greenhouse | [Apply](https://boards.greenhouse.io/figma/jobs/5621177004?gh_jid=5621177004) |
| 2 | 6.5/10 | Cloudflare | Software Engineer Intern (Summer 2026) - Austin, TX | In-Office | greenhouse | [Apply](https://boards.greenhouse.io/cloudflare/jobs/7206269?gh_jid=7206269) |
| 3 | 6.2/10 | Cloudflare | Software Engineer, AI - Lisbon | Hybrid | greenhouse | [Apply](https://boards.greenhouse.io/cloudflare/jobs/6998511?gh_jid=6998511) |
| 4 | 6.2/10 | Cloudflare | Software Engineer - Network Services | Hybrid | greenhouse | [Apply](https://boards.greenhouse.io/cloudflare/jobs/7343760?gh_jid=7343760) |
| 5 | 5.8/10 | Cloudflare | Software Engineer Intern (Summer 2026) | In-Office | greenhouse | [Apply](https://boards.greenhouse.io/cloudflare/jobs/7296923?gh_jid=7296923) |
| 6 | 5.0/10 | Cloudflare | Software Engineer, Application Performance | Hybrid | greenhouse | [Apply](https://boards.greenhouse.io/cloudflare/jobs/7261038?gh_jid=7261038) |
| 7 | 4.5/10 | Cloudflare | Software Engineer (Backend) | In-Office | greenhouse | [Apply](https://boards.greenhouse.io/cloudflare/jobs/7603643?gh_jid=7603643) |
| 8 | 4.5/10 | Cloudflare | Software Engineer, R2 Storage | Hybrid | greenhouse | [Apply](https://boards.greenhouse.io/cloudflare/jobs/7104127?gh_jid=7104127) |
| 9 | 4.5/10 | Cloudflare | Software Engineer, Enterprise Readiness | Hybrid | greenhouse | [Apply](https://boards.greenhouse.io/cloudflare/jobs/6467350?gh_jid=6467350) |
| 10 | 4.2/10 | Cloudflare | Software Engineer, KV  | Hybrid | greenhouse | [Apply](https://boards.greenhouse.io/cloudflare/jobs/7493433?gh_jid=7493433) |
| 11 | 4.0/10 | Cloudflare | Network Software Engineer | Hybrid | greenhouse | [Apply](https://boards.greenhouse.io/cloudflare/jobs/7343755?gh_jid=7343755) |
| 12 | 3.5/10 | Cloudflare | Senior Software Engineer (Full Stack) | In-Office | greenhouse | [Apply](https://boards.greenhouse.io/cloudflare/jobs/7566807?gh_jid=7566807) |
| 13 | 3.5/10 | Cloudflare | Software Engineer, Cloudforce One | Hybrid | greenhouse | [Apply](https://boards.greenhouse.io/cloudflare/jobs/7309174?gh_jid=7309174) |
| 14 | 3.5/10 | Cloudflare | Software Engineer , AI Agents Tooling & Platforms  | Hybrid | greenhouse | [Apply](https://boards.greenhouse.io/cloudflare/jobs/5879768?gh_jid=5879768) |
| 15 | 3.5/10 | Cloudflare | Senior Software Engineer - Network Dev | In-Office | greenhouse | [Apply](https://boards.greenhouse.io/cloudflare/jobs/7167953?gh_jid=7167953) |
| 16 | 3.5/10 | Cloudflare | Senior Software Engineer, AI Applications Tooling | Hybrid | greenhouse | [Apply](https://boards.greenhouse.io/cloudflare/jobs/6628327?gh_jid=6628327) |
| 17 | 3.5/10 | Cloudflare | Software Engineer- AI | In-Office | greenhouse | [Apply](https://boards.greenhouse.io/cloudflare/jobs/7603196?gh_jid=7603196) |
| 18 | 3.0/10 | Iteration One GmbH | Software Engineer, Game Development (f/m/d) | Karlsruhe | arbeitnow | [Apply](https://www.arbeitnow.com/jobs/companies/iteration-one-gmbh/software-engineer-game-development-karlsruhe-245798) |
| 19 | 3.0/10 | 1KOMMA5˚ | Senior Software Engineer - Energy Markets (m/f/d) | Berlin | arbeitnow | [Apply](https://www.arbeitnow.com/jobs/companies/1komma50/senior-software-engineer-energy-markets-berlin-425979) |
| 20 | 3.0/10 | 1KOMMA5˚ | Senior Backend VPP Software Engineer - TypeScript (m/f/d) | Berlin | arbeitnow | [Apply](https://www.arbeitnow.com/jobs/companies/1komma50/senior-backend-vpp-software-engineer-typescript-berlin-340536) |

### Detailed Job Analysis

#### 1. Software Engineer Intern, Developer Tools (2026) (London, United Kingdom) at Figma

- **Overall Score:** 6.8/10
- **Breakdown:** Skills: 9/10 | Experience: 8/10 | Education: 10/10 | Location: 2/10 | Salary: 5/10
- **Location:** London, England
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/figma/jobs/5621177004?gh_jid=5621177004

**Analysis:** The candidate possesses excellent technical skills, including strong proficiency in React, TypeScript, and AI/LLM integrations, which perfectly align with Figma's Developer Tools and AI initiatives. However, the overall match is significantly hindered by a location mismatch (London vs. North America/Remote preferences) and a potential timeline conflict, as the candidate graduates in late 2025 for a 2026 internship role.

**Strengths (Why it fits):**
- Strong proficiency in JavaScript, TypeScript, and React, which are core to Figma's tech stack.
- Extensive experience building AI-assisted tools, RAG pipelines, and LLM agents, highly relevant to Figma's AI-assisted code translation goals.
- Solid academic foundation with a Master's in Electrical and Computer Engineering and a high GPA.
- Proven ability to build end-to-end full-stack applications and data pipelines.

**Gaps (Why it may not fit):**
- Redux
- WebAssembly

#### 2. Software Engineer Intern (Summer 2026) - Austin, TX at Cloudflare

- **Overall Score:** 6.5/10
- **Breakdown:** Skills: 8/10 | Experience: 9/10 | Education: 3/10 | Location: 7/10 | Salary: 5/10
- **Location:** In-Office
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/cloudflare/jobs/7206269?gh_jid=7206269

**Analysis:** The candidate possesses strong technical skills in Python, C++, and TypeScript, along with impressive internship experience building production-grade systems. However, there is a significant timeline mismatch: the candidate is scheduled to graduate in October 2025, making them likely ineligible for a Summer 2026 internship which requires currently enrolled students.

**Strengths (Why it fits):**
- Proficiency in key languages used at Cloudflare, including Python, C++, and JavaScript/TypeScript.
- Demonstrated passion for software development through complex personal projects and research.
- Solid foundation in backend development, microservices, and containerization (Docker, FastAPI).

**Gaps (Why it may not fit):**
- Go
- Rust
- Experience with Cloudflare developer platform (Bonus)

#### 3. Software Engineer, AI - Lisbon at Cloudflare

- **Overall Score:** 6.2/10
- **Breakdown:** Skills: 8/10 | Experience: 6/10 | Education: 10/10 | Location: 2/10 | Salary: 5/10
- **Location:** Hybrid
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/cloudflare/jobs/6998511?gh_jid=6998511

**Analysis:** The candidate possesses strong AI/ML skills and relevant experience in TypeScript/JavaScript, matching the technical and bonus requirements well. However, the significant location mismatch (Lisbon vs. North America) and potential salary expectation gap lower the overall fit.

**Strengths (Why it fits):**
- Strong AI/ML expertise including RAG, LLMs, and Computer Vision
- Proficiency in TypeScript and JavaScript
- Solid educational background in Computer Engineering
- Experience with containerization (Docker) and backend APIs (FastAPI, Node.js)

**Gaps (Why it may not fit):**
- Rust programming language
- Deep Linux/UNIX systems knowledge
- WebAssembly
- Extensive full-time production experience

#### 4. Software Engineer - Network Services at Cloudflare

- **Overall Score:** 6.2/10
- **Breakdown:** Skills: 6/10 | Experience: 7/10 | Education: 9/10 | Location: 4/10 | Salary: 5/10
- **Location:** Hybrid
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/cloudflare/jobs/7343760?gh_jid=7343760

**Analysis:** The candidate has a strong educational background in Computer Engineering and solid backend/API development skills. However, their experience is heavily skewed towards AI/ML and Computer Vision, whereas the role emphasizes network protocols, distributed systems, and systems-level programming. Additionally, there is a location mismatch as the role requires hybrid work in specific cities (Austin, London, Lisbon) while the candidate is based in Canada.

**Strengths (Why it fits):**
- Strong educational background in Computer Engineering (BASc and MEng)
- Experience designing and building APIs (FastAPI, REST APIs)
- Experience with relational databases (PostgreSQL) and containerization (Docker)
- Proficient in multiple programming languages including C++, Python, Java, and JavaScript

**Gaps (Why it may not fit):**
- Go or Rust programming languages
- Deep understanding of network protocols (TCP/IP, TLS, HTTP)
- Experience with high-volume distributed systems
- Unix systems-level programming

#### 5. Software Engineer Intern (Summer 2026) at Cloudflare

- **Overall Score:** 5.8/10
- **Breakdown:** Skills: 8/10 | Experience: 9/10 | Education: 6/10 | Location: 1/10 | Salary: 5/10
- **Location:** In-Office
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/cloudflare/jobs/7296923?gh_jid=7296923

**Analysis:** The candidate possesses strong technical skills and relevant internship experience that align well with Cloudflare's engineering stack. However, there is a major location mismatch (London vs. North America/Remote) and a timeline conflict, as the candidate graduates in October 2025 for a Summer 2026 internship.

**Strengths (Why it fits):**
- Proficiency in Python, C++, and TypeScript/JavaScript, which are key languages at Cloudflare.
- Proven track record of building production-grade systems and data pipelines during previous internships.
- Demonstrated passion for software development through complex, full-stack personal projects.

**Gaps (Why it may not fit):**
- Go
- Rust
- Cloudflare Developer Platform experience

#### 6. Software Engineer, Application Performance at Cloudflare

- **Overall Score:** 5.0/10
- **Breakdown:** Skills: 4/10 | Experience: 2/10 | Education: 10/10 | Location: 6/10 | Salary: 5/10
- **Location:** Hybrid
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/cloudflare/jobs/7261038?gh_jid=7261038

**Analysis:** The candidate has an excellent educational background in Computer Engineering but falls significantly short of the desired 4+ years of professional experience. Additionally, their skill set is heavily focused on AI/ML and full-stack development, whereas the role requires deep expertise in distributed systems, networking protocols, and systems-level programming.

**Strengths (Why it fits):**
- Strong educational foundation with a Master's and Bachelor's in Computer Engineering
- Experience with PostgreSQL, Git, and Docker
- Demonstrated ability to architect and deploy complex software pipelines

**Gaps (Why it may not fit):**
- 4+ years of professional software engineering experience
- Systems-level programming languages (Go, Rust)
- Deep understanding of networking protocols (TCP/QUIC, HTTP, Linux networking)
- Experience building and debugging high-volume distributed systems
- Monitoring and alerting for production systems

#### 7. Software Engineer (Backend) at Cloudflare

- **Overall Score:** 4.5/10
- **Breakdown:** Skills: 6/10 | Experience: 2/10 | Education: 9/10 | Location: 4/10 | Salary: 5/10
- **Location:** In-Office
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/cloudflare/jobs/7603643?gh_jid=7603643

**Analysis:** The candidate has a strong educational background and solid foundational skills in Python, TypeScript, and AI/ML integrations. However, they lack the required 3-5+ years of enterprise experience and specific expertise in developing Model Context Protocol (MCP) servers and Infrastructure as Code (Terraform/Ansible) mandated by the role.

**Strengths (Why it fits):**
- Strong programming skills in Python and TypeScript.
- Experience building AI/ML pipelines, specifically RAG and LLM integrations.
- Solid backend development experience with FastAPI, REST APIs, and Docker.

**Gaps (Why it may not fit):**
- Model Context Protocol (MCP) server development
- 3-5+ years of enterprise experience
- Infrastructure as Code (Terraform, Ansible, Chef)
- CI/CD pipeline development (GitLab/GitHub Actions)
- Go (programming language)

#### 8. Software Engineer, R2 Storage at Cloudflare

- **Overall Score:** 4.5/10
- **Breakdown:** Skills: 4/10 | Experience: 3/10 | Education: 8/10 | Location: 4/10 | Salary: 5/10
- **Location:** Hybrid
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/cloudflare/jobs/7104127?gh_jid=7104127

**Analysis:** The candidate has a strong academic background in Computer Engineering and solid internship experience in AI/ML and backend development. However, they lack the specific distributed storage systems experience and key programming languages (Rust, Go) required for the Cloudflare R2 team, and are currently a student with only internship-level experience.

**Strengths (Why it fits):**
- Academic foundation in Computer Engineering
- Experience with TypeScript in full-stack projects
- Familiarity with high-throughput backend technologies like Kafka, Redis, and Docker
- Strong problem-solving skills demonstrated through complex architectural projects

**Gaps (Why it may not fit):**
- Rust
- Go
- Distributed storage systems
- Consensus algorithms
- Data replication

#### 9. Software Engineer, Enterprise Readiness at Cloudflare

- **Overall Score:** 4.5/10
- **Breakdown:** Skills: 6/10 | Experience: 2/10 | Education: 9/10 | Location: 5/10 | Salary: 5/10
- **Location:** Hybrid
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/cloudflare/jobs/6467350?gh_jid=6467350

**Analysis:** The candidate possesses a strong educational background and impressive projects in AI and full-stack development, aligning well with the job's interest in Agentic AI. However, the role requires 3+ years of professional backend experience and proficiency in Go and Kubernetes, whereas the candidate is at the entry/intern level with a Python/JS focus.

**Strengths (Why it fits):**
- Strong academic background in Computer Engineering (Master's and Bachelor's).
- Direct experience with Agentic AI development (LangGraph, RAG), which is explicitly mentioned as a desirable skill.
- Familiarity with full-stack development and core technologies like React, TypeScript, PostgreSQL, Redis, and Docker.

**Gaps (Why it may not fit):**
- Go (Golang)
- Kubernetes
- Observability tools (Kibana, Jaeger, Sentry, Elasticsearch)
- PHP
- 3+ years of professional backend experience

#### 10. Software Engineer, KV  at Cloudflare

- **Overall Score:** 4.2/10
- **Breakdown:** Skills: 5/10 | Experience: 2/10 | Education: 8/10 | Location: 1/10 | Salary: 5/10
- **Location:** Hybrid
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/cloudflare/jobs/7493433?gh_jid=7493433

**Analysis:** The candidate has a strong academic background in computer engineering and AI/ML, but lacks the required 2+ years of high-volume production software experience and specific systems programming languages like Go or Rust. Furthermore, there is a complete mismatch in location preferences, as the role requires hybrid work in Lisbon or London, while the candidate prefers North America or remote.

**Strengths (Why it fits):**
- Proficiency in C++ and JavaScript
- Experience building APIs and working with data pipelines
- Strong academic foundation in Computer Engineering
- Hands-on experience with Redis, which is relevant to key-value store development

**Gaps (Why it may not fit):**
- Go
- Rust
- 2+ years of high-volume production experience
- Distributed systems at scale
- Monitoring and alerting tools

#### 11. Network Software Engineer at Cloudflare

- **Overall Score:** 4.0/10
- **Breakdown:** Skills: 2/10 | Experience: 3/10 | Education: 7/10 | Location: 3/10 | Salary: 5/10
- **Location:** Hybrid
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/cloudflare/jobs/7343755?gh_jid=7343755

**Analysis:** The candidate has a strong background in AI/ML and full-stack development, but lacks the core networking and systems programming (Go/Rust) skills required for this Network Software Engineer role. Additionally, the hybrid location requirement in Austin, London, or Lisbon conflicts with the candidate's current location in Canada and preference for remote work.

**Strengths (Why it fits):**
- Experience with public clouds (AWS, Azure) and containerization (Docker)
- Experience designing and integrating RESTful APIs and backend systems
- Strong educational background in Computer Engineering with high GPA

**Gaps (Why it may not fit):**
- Go or Rust programming
- Layer 3 and Layer 4 networking (VPCs, BGP, GRE tunnels)
- Network engineering protocols (OSPF, MPLS)
- Kubernetes
- Prometheus
- Network orchestration platforms

#### 12. Senior Software Engineer (Full Stack) at Cloudflare

- **Overall Score:** 3.5/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 10/10 | Location: 1/10 | Salary: 3/10
- **Location:** In-Office
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/cloudflare/jobs/7566807?gh_jid=7566807

**Analysis:** The candidate has relevant technical skills in Python, React, and AI technologies, along with a matching educational background. However, they fall significantly short of the 6+ years of required experience and have conflicting location preferences (Bengaluru in-office vs. North America/Remote).

**Strengths (Why it fits):**
- Strong educational background with a B.A.Sc and ongoing M.Eng in relevant engineering fields.
- Relevant full-stack tech stack experience including Python, Java, React, TypeScript, and PostgreSQL.
- Hands-on experience with AI components, vector databases (Milvus, ChromaDB), and RAG pipelines, which is a highlighted requirement.

**Gaps (Why it may not fit):**
- 6+ years of professional experience
- Go
- Scala
- ClickHouse
- Mentorship experience
- System architecture at scale

#### 13. Software Engineer, Cloudforce One at Cloudflare

- **Overall Score:** 3.5/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 8/10 | Location: 4/10 | Salary: 5/10
- **Location:** Hybrid
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/cloudflare/jobs/7309174?gh_jid=7309174

**Analysis:** The candidate possesses several relevant technical skills including TypeScript, PostgreSQL, REST APIs, and Redis, along with a strong educational background. However, they fall significantly short of the 5+ years of required experience, as they only have internship-level experience, making them a poor fit for this mid-to-senior level role.

**Strengths (Why it fits):**
- Experience with TypeScript, PostgreSQL, and REST APIs
- Familiarity with nice-to-have technologies like Kafka, React, and Redis
- Demonstrated ability to write well-tested code (80%+ coverage in projects)

**Gaps (Why it may not fit):**
- 5+ years of software engineering experience
- Go (Golang)
- Rust
- Kubernetes
- Trust & Safety or Legal domain experience

#### 14. Software Engineer , AI Agents Tooling & Platforms  at Cloudflare

- **Overall Score:** 3.5/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 9/10 | Location: 1/10 | Salary: 5/10
- **Location:** Hybrid
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/cloudflare/jobs/5879768?gh_jid=5879768

**Analysis:** While the candidate has strong foundational knowledge in AI frameworks and TypeScript, they fall significantly short of the 5+ years of required experience. Additionally, the candidate's location preferences (North America/Remote) conflict with the hybrid requirement in Lisbon or London.

**Strengths (Why it fits):**
- Hands-on experience building AI agents and RAG pipelines using LangChain and LangGraph.
- Proficiency in TypeScript, JavaScript, and C++.
- Strong academic background with a Master's degree in Electrical and Computer Engineering.

**Gaps (Why it may not fit):**
- 5+ years of professional software engineering experience.
- Go or Rust programming languages.
- Experience with high-volume, large-scale distributed systems.
- Cloudflare Workers development experience.

#### 15. Senior Software Engineer - Network Dev at Cloudflare

- **Overall Score:** 3.5/10
- **Breakdown:** Skills: 4/10 | Experience: 1/10 | Education: 9/10 | Location: 1/10 | Salary: 5/10
- **Location:** In-Office
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/cloudflare/jobs/7167953?gh_jid=7167953

**Analysis:** The candidate is a current master's student with only internship experience, falling significantly short of the 5+ years required for this senior-level role. Furthermore, the position is located in Bengaluru (In-Office), which directly conflicts with the candidate's preferences for Remote, US, or Canada.

**Strengths (Why it fits):**
- Strong educational background with degrees in Computer Engineering and Electrical and Computer Engineering.
- Proficiency in Python and SQL (PostgreSQL).
- Hands-on experience with containerization using Docker.

**Gaps (Why it may not fit):**
- 5+ years of software development experience
- Network automation
- Golang
- Observability systems (Prometheus, Grafana)
- CI/CD pipelines
- Layer 2 and Layer 3 networking protocols

#### 16. Senior Software Engineer, AI Applications Tooling at Cloudflare

- **Overall Score:** 3.5/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 8/10 | Location: 3/10 | Salary: 5/10
- **Location:** Hybrid
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/cloudflare/jobs/6628327?gh_jid=6628327

**Analysis:** The candidate possesses relevant foundational skills in AI, LLMs, and modern agent patterns, which aligns well with the job's technical focus. However, they are currently a student with only internship experience, falling drastically short of the 5+ years of professional experience required for this senior-level role.

**Strengths (Why it fits):**
- Hands-on experience with LLMs, RAG, and modern agent patterns (LangGraph)
- Proficiency in TypeScript and full-stack development
- Experience building AI evaluation pipelines using RAGAS

**Gaps (Why it may not fit):**
- 5+ years of professional software engineering experience
- Cloudflare platform or edge/serverless architectures
- Large-scale distributed systems experience
- Security depth (prompt injection protection, PII handling, secrets management)

#### 17. Software Engineer- AI at Cloudflare

- **Overall Score:** 3.5/10
- **Breakdown:** Skills: 6/10 | Experience: 2/10 | Education: 8/10 | Location: 1/10 | Salary: 3/10
- **Location:** In-Office
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/cloudflare/jobs/7603196?gh_jid=7603196

**Analysis:** The candidate possesses relevant technical skills in AI, LLMs, and LangChain, but falls significantly short of the 5+ years of required experience. Furthermore, there is a complete mismatch in location, as the role is in-office in Bengaluru, India, while the candidate prefers North America or remote work.

**Strengths (Why it fits):**
- Hands-on experience with LangChain, RAG, and LLM application development.
- Proficiency in TypeScript and building full-stack AI applications.
- Experience deploying applications using Docker and FastAPI.

**Gaps (Why it may not fit):**
- 5+ years of software development experience
- Cloudflare AI Gateway
- Kubernetes (K8s)
- Terraform
- Observability tools (Grafana, OTEL)

#### 18. Software Engineer, Game Development (f/m/d) at Iteration One GmbH

- **Overall Score:** 3.0/10
- **Breakdown:** Skills: 3/10 | Experience: 2/10 | Education: 8/10 | Location: 1/10 | Salary: 3/10
- **Location:** Karlsruhe
- **Source:** arbeitnow
- **Apply URL:** https://www.arbeitnow.com/jobs/companies/iteration-one-gmbh/software-engineer-game-development-karlsruhe-245798

**Analysis:** The candidate possesses a strong AI background that aligns well with the company's vision, but lacks the core C# and Unity skills required for the role. Furthermore, the candidate's location preferences and salary expectations are highly incompatible with an on-site role in Germany.

**Strengths (Why it fits):**
- Extensive hands-on experience with AI, LLMs, and RAG pipelines, matching the company's AI-first culture.
- Background in mobile app development and Android Studio.
- Strong academic foundation in Software and Computer Engineering.

**Gaps (Why it may not fit):**
- C#
- Unity
- Live game operations
- Game performance optimization
- UniRx

#### 19. Senior Software Engineer - Energy Markets (m/f/d) at 1KOMMA5˚

- **Overall Score:** 3.0/10
- **Breakdown:** Skills: 3/10 | Experience: 1/10 | Education: 7/10 | Location: 1/10 | Salary: 5/10
- **Location:** Berlin
- **Source:** arbeitnow
- **Apply URL:** https://www.arbeitnow.com/jobs/companies/1komma50/senior-software-engineer-energy-markets-berlin-425979

**Analysis:** The candidate is a recent graduate with internship experience, whereas the role requires a Senior Software Engineer with leadership capabilities and specific domain knowledge in energy markets. Additionally, there is a geographic mismatch as the role is based in Germany and the candidate prefers North America.

**Strengths (Why it fits):**
- Strong background in Python and backend development
- Experience with data pipelines and processing
- Solid educational foundation in Computer Engineering

**Gaps (Why it may not fit):**
- Senior-level architectural and mentoring experience
- TypeScript
- GCP (Google Cloud Platform)
- Energy market domain knowledge
- CI/CD

#### 20. Senior Backend VPP Software Engineer - TypeScript (m/f/d) at 1KOMMA5˚

- **Overall Score:** 3.0/10
- **Breakdown:** Skills: 3/10 | Experience: 1/10 | Education: 7/10 | Location: 1/10 | Salary: 5/10
- **Location:** Berlin
- **Source:** arbeitnow
- **Apply URL:** https://www.arbeitnow.com/jobs/companies/1komma50/senior-backend-vpp-software-engineer-typescript-berlin-340536

**Analysis:** The candidate is a recent graduate with internship experience, whereas the role requires a Senior Backend Engineer with specific domain expertise in virtual power plants and energy markets. Additionally, there is a geographic mismatch as the role is based in Germany and the candidate prefers North America.

**Strengths (Why it fits):**
- Python experience (listed as a bonus requirement)
- Backend development experience (Node.js, FastAPI, Docker)
- Strong educational background in Computer Engineering

**Gaps (Why it may not fit):**
- Senior-level backend experience
- Virtual Power Plant (VPP) and energy market integration
- NestJS
- Google Cloud Platform (GCP)
- Terraform
- CI/CD with GitHub Actions

---
## Search: "AI Engineer"

**Jobs Scraped:** 32 unique
**Jobs Scored:** 20
**Sources:** greenhouse, arbeitnow
**Duration:** 426.9s

**Average Score:** 4.7/10

### Match Results Overview

| # | Score | Company | Title | Location | Source | Apply Link |
|---|-------|---------|-------|----------|--------|------------|
| 1 | 7.4/10 | Cloudflare | Software Engineer Intern (Summer 2026) - Austin, TX | In-Office | greenhouse | N/A |
| 2 | 6.8/10 | Figma | Software Engineer Intern, Developer Tools (2026) (London, United Kingdom) | London, England | greenhouse | N/A |
| 3 | 6.0/10 | Databricks | AI Engineer - FDE (Forward Deployed Engineer) | Melbourne, Australia | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8330188002) |
| 4 | 6.0/10 | Databricks | AI Engineer - FDE (Forward Deployed Engineer) | Sydney, Australia | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8298792002) |
| 5 | 5.6/10 | Databricks | AI Engineer - FDE (Forward Deployed Engineer) | Amsterdam, Netherlands | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8189900002) |
| 6 | 5.5/10 | Cloudflare | Software Engineer Intern (Summer 2026) | In-Office | greenhouse | N/A |
| 7 | 5.5/10 | Databricks | AI Engineer - FDE (Forward Deployed Engineer) | Canada | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8419885002) |
| 8 | 5.5/10 | Cloudflare | Software Engineer, AI - Lisbon | Hybrid | greenhouse | N/A |
| 9 | 5.4/10 | Databricks | AI Engineer - FDE (Forward Deployed Engineer) | London, United Kingdom | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8024004002) |
| 10 | 5.0/10 | Databricks | AI Engineer - FDE (Forward Deployed Engineer) | Munich, Germany | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8395599002) |
| 11 | 4.5/10 | Cloudflare | Software Engineer , AI Agents Tooling & Platforms  | Hybrid | greenhouse | N/A |
| 12 | 4.0/10 | Databricks | AI Engineer - FDE (Forward Deployed Engineer) | Paris, France | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8395601002) |
| 13 | 4.0/10 | Cloudflare | Software Engineer, R2 Storage | Hybrid | greenhouse | N/A |
| 14 | 4.0/10 | Databricks | AI Engineer - FDE (Forward Deployed Engineer) | Remote - India | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8099751002) |
| 15 | 4.0/10 | Cloudflare | Software Engineer (Backend) | In-Office | greenhouse | N/A |
| 16 | 3.5/10 | Cloudflare | Senior Software Engineer, AI Applications Tooling | Hybrid | greenhouse | N/A |
| 17 | 3.0/10 | 1KOMMA5˚ | Senior Software Engineer - Energy Markets (m/f/d) | Berlin | arbeitnow | N/A |
| 18 | 3.0/10 | Iteration One GmbH | Software Engineer, Game Development (f/m/d) | Karlsruhe | arbeitnow | N/A |
| 19 | 3.0/10 | 1KOMMA5˚ | Senior Backend VPP Software Engineer - TypeScript (m/f/d) | Berlin | arbeitnow | N/A |
| 20 | 3.0/10 | Cloudflare | Senior Software Engineer (Full Stack) | In-Office | greenhouse | N/A |

### Detailed Job Analysis

#### 1. Software Engineer Intern (Summer 2026) - Austin, TX at Cloudflare

- **Overall Score:** 7.4/10
- **Breakdown:** Skills: 9/10 | Experience: 9/10 | Education: 6/10 | Location: 8/10 | Salary: 5/10
- **Location:** In-Office
- **Source:** greenhouse

**Analysis:** The candidate has an excellent technical background with strong proficiency in Python, C++, and TypeScript, matching Cloudflare's tech stack. However, their expected graduation in October 2025 may make them ineligible for a Summer 2026 internship unless they plan to pursue further education.

**Strengths (Why it fits):**
- Proficiency in Python, C++, and JavaScript/TypeScript
- Relevant software engineering internship experience
- Strong portfolio of complex, full-stack personal projects
- Currently pursuing a highly relevant Master's degree in Electrical and Computer Engineering

**Gaps (Why it may not fit):**
- Go
- Rust

#### 2. Software Engineer Intern, Developer Tools (2026) (London, United Kingdom) at Figma

- **Overall Score:** 6.8/10
- **Breakdown:** Skills: 9/10 | Experience: 8/10 | Education: 10/10 | Location: 2/10 | Salary: 5/10
- **Location:** London, England
- **Source:** greenhouse

**Analysis:** The candidate possesses strong technical skills, particularly in React, JavaScript, C++, and AI/ML, which align perfectly with Figma's DevTools stack and AI initiatives. However, there is a significant location mismatch as the role is based in London, while the candidate prefers Remote, US, or Canada, and the 2026 internship timeline may conflict with their 2025 graduation.

**Strengths (Why it fits):**
- Strong proficiency in required languages and frameworks (JavaScript, React, C++, Python).
- Relevant experience building AI/ML pipelines and LLM applications, aligning with Figma's AI-assisted design-to-code tools.
- Solid foundation in core CS concepts and full-stack development.
- Previous software engineering internship experience demonstrating ability to ship technical projects.

**Gaps (Why it may not fit):**
- WebAssembly
- Redux

#### 3. AI Engineer - FDE (Forward Deployed Engineer) at Databricks

- **Overall Score:** 6.0/10
- **Breakdown:** Skills: 7/10 | Experience: 2/10 | Education: 8/10 | Location: 8/10 | Salary: 5/10
- **Location:** Melbourne, Australia
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=8330188002

**Analysis:** The candidate possesses highly relevant technical skills in GenAI, RAG, and LangChain, aligning well with the core technical requirements of the role. However, the candidate is still completing their Master's degree and lacks the 'extensive years of hands-on industry data science experience' required for this customer-facing Forward Deployed Engineer position.

**Strengths (Why it fits):**
- Hands-on experience building and deploying production-grade RAG systems and multi-agent pipelines.
- Proficiency with required tools like LangChain, LangGraph, and vector databases (Milvus, ChromaDB).
- Experience with GenAI evaluation frameworks (RAGAS, LLM self-critique).
- Pursuing a relevant graduate degree in Electrical and Computer Engineering.

**Gaps (Why it may not fit):**
- Extensive industry data science experience
- PyTorch, pandas, scikit-learn
- DSPy
- Databricks Intelligence Platform
- Apache Spark
- Customer-facing or technical advisory experience

#### 4. AI Engineer - FDE (Forward Deployed Engineer) at Databricks

- **Overall Score:** 6.0/10
- **Breakdown:** Skills: 8/10 | Experience: 3/10 | Education: 9/10 | Location: 7/10 | Salary: 5/10
- **Location:** Sydney, Australia
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=8298792002

**Analysis:** The candidate possesses highly relevant technical skills in GenAI, RAG, and multi-agent systems, directly aligning with the core technical requirements of the role. However, the position calls for 'extensive years of hands-on industry data science experience' and a customer-facing advisory capacity, whereas the candidate is currently a Master's student with only internship-level experience.

**Strengths (Why it fits):**
- Hands-on experience building production-grade RAG systems and multi-agent pipelines using LangChain and LangGraph.
- Experience with GenAI evaluation frameworks like RAGAS and LLM self-critique.
- Graduate degree in Electrical and Computer Engineering (in progress).
- Experience deploying ML models using Docker, FastAPI, and cloud platforms (AWS, Azure).

**Gaps (Why it may not fit):**
- Extensive years of industry data science experience
- Customer-facing or technical advisory experience
- Databricks Intelligence Platform and Apache Spark
- DSPy
- Text2SQL

#### 5. AI Engineer - FDE (Forward Deployed Engineer) at Databricks

- **Overall Score:** 5.6/10
- **Breakdown:** Skills: 8/10 | Experience: 3/10 | Education: 10/10 | Location: 2/10 | Salary: 5/10
- **Location:** Amsterdam, Netherlands
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=8189900002

**Analysis:** The candidate possesses highly relevant technical skills in GenAI, RAG, and LangChain, perfectly aligning with the core technical requirements of the role. However, the candidate lacks the 'extensive years' of industry experience requested and is located in Canada, which conflicts with the European location requirements of the job.

**Strengths (Why it fits):**
- Hands-on experience building and evaluating RAG pipelines and multi-agent systems using LangChain and LangGraph.
- Experience deploying ML/GenAI applications using Docker, FastAPI, AWS, and Azure.
- Graduate degree in Electrical and Computer Engineering.

**Gaps (Why it may not fit):**
- Extensive industry data science experience (pandas, scikit-learn)
- Databricks Intelligence Platform and Apache Spark
- DSPy and HuggingFace
- Customer-facing or technical advisory experience

#### 6. Software Engineer Intern (Summer 2026) at Cloudflare

- **Overall Score:** 5.5/10
- **Breakdown:** Skills: 8/10 | Experience: 9/10 | Education: 5/10 | Location: 1/10 | Salary: 5/10
- **Location:** In-Office
- **Source:** greenhouse

**Analysis:** The candidate possesses strong technical skills and relevant software engineering internship experience that align well with Cloudflare's tech stack. However, there are major mismatches regarding location (London vs. North America/Remote) and internship eligibility, as the candidate is scheduled to graduate in October 2025, well before the Summer 2026 internship.

**Strengths (Why it fits):**
- Proficiency in key languages mentioned in the job description, including Python, C++, and JavaScript/TypeScript
- Demonstrated ability to build and deploy end-to-end software pipelines and full-stack applications
- Strong academic background in Computer Engineering and Software Engineering
- Proactive in building complex personal projects, which aligns with the company's desired traits

**Gaps (Why it may not fit):**
- Go
- Rust

#### 7. AI Engineer - FDE (Forward Deployed Engineer) at Databricks

- **Overall Score:** 5.5/10
- **Breakdown:** Skills: 7/10 | Experience: 2/10 | Education: 9/10 | Location: 10/10 | Salary: 10/10
- **Location:** Canada
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=8419885002

**Analysis:** The candidate possesses highly relevant GenAI skills, including RAG and LangChain, and meets the educational and location requirements. However, the role requires extensive industry experience, whereas the candidate is a current student with only internship-level experience.

**Strengths (Why it fits):**
- Hands-on experience with RAG, LangChain, and multi-agent systems (LangGraph)
- Experience with GenAI evaluation frameworks like RAGAS
- Pursuing a relevant Master's degree in Electrical and Computer Engineering
- Location and salary expectations align perfectly with the role

**Gaps (Why it may not fit):**
- Extensive years of industry data science experience
- Databricks Intelligence Platform
- Apache Spark
- DSPy
- Text2SQL
- PyTorch, pandas, scikit-learn

#### 8. Software Engineer, AI - Lisbon at Cloudflare

- **Overall Score:** 5.5/10
- **Breakdown:** Skills: 8/10 | Experience: 5/10 | Education: 10/10 | Location: 2/10 | Salary: 5/10
- **Location:** Hybrid
- **Source:** greenhouse

**Analysis:** The candidate possesses strong AI and TypeScript skills along with an excellent educational background that matches the job requirements. However, there is a significant location mismatch as the role is hybrid in Lisbon while the candidate prefers North America or remote work, and their professional background consists primarily of internships rather than proven full-time experience.

**Strengths (Why it fits):**
- Strong educational background with a Bachelor's and Master's in Computer/Electrical Engineering.
- Hands-on experience with AI solutions, including RAG, LLMs, and Computer Vision.
- Proficiency in TypeScript and JavaScript, which are key languages for the role.
- Experience with operational deployment using Docker, FastAPI, and Redis.

**Gaps (Why it may not fit):**
- Rust programming language
- Deep Linux/UNIX systems or kernel knowledge
- WebAssembly
- Proven full-time industry experience

#### 9. AI Engineer - FDE (Forward Deployed Engineer) at Databricks

- **Overall Score:** 5.4/10
- **Breakdown:** Skills: 7/10 | Experience: 4/10 | Education: 9/10 | Location: 2/10 | Salary: 5/10
- **Location:** London, United Kingdom
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=8024004002

**Analysis:** The candidate possesses highly relevant technical skills in GenAI, RAG, and LangChain, and is pursuing the required graduate degree. However, the candidate falls short on the 'extensive years' of industry experience requested and has a major location mismatch, as the role is in London while the candidate prefers North America.

**Strengths (Why it fits):**
- Hands-on experience building and deploying RAG pipelines and multi-agent systems using LangChain and LangGraph.
- Experience with production deployments using Docker, FastAPI, and cloud platforms (AWS, Azure).
- Pursuing a Master's degree in Electrical and Computer Engineering, meeting the graduate degree requirement.
- Experience with GenAI evaluation frameworks like RAGAS.

**Gaps (Why it may not fit):**
- Extensive industry data science experience (pandas, scikit-learn, PyTorch)
- Databricks Intelligence Platform
- Apache Spark
- DSPy
- Text2SQL

#### 10. AI Engineer - FDE (Forward Deployed Engineer) at Databricks

- **Overall Score:** 5.0/10
- **Breakdown:** Skills: 7/10 | Experience: 3/10 | Education: 8/10 | Location: 2/10 | Salary: 5/10
- **Location:** Munich, Germany
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=8395599002

**Analysis:** The candidate possesses highly relevant technical skills in GenAI, RAG, and LangChain, aligning well with the core technical requirements of the role. However, the candidate lacks the 'extensive years' of industry experience required and is located in Canada, which conflicts with the European location requirements of the job.

**Strengths (Why it fits):**
- Hands-on experience building and evaluating production-grade RAG pipelines using LangChain and RAGAS.
- Experience with multi-agent systems (LangGraph) and vector databases (Milvus, ChromaDB).
- Pursuing a relevant Master's degree in Electrical and Computer Engineering.
- Experience deploying ML models using Docker, FastAPI, and cloud platforms (AWS, Azure).

**Gaps (Why it may not fit):**
- Extensive years of industry data science experience
- PyTorch, pandas, scikit-learn
- Databricks Intelligence Platform and Apache Spark
- DSPy
- HuggingFace

#### 11. Software Engineer , AI Agents Tooling & Platforms  at Cloudflare

- **Overall Score:** 4.5/10
- **Breakdown:** Skills: 6/10 | Experience: 2/10 | Education: 9/10 | Location: 1/10 | Salary: 5/10
- **Location:** Hybrid
- **Source:** greenhouse

**Analysis:** The candidate possesses highly relevant technical skills in AI agents, TypeScript, and C++, aligning well with the team's focus on AI tooling. However, the role requires 5+ years of experience and is located in Lisbon or London, which severely mismatches the candidate's entry-level status and North American location preferences.

**Strengths (Why it fits):**
- Hands-on experience building AI agent pipelines using LangGraph and LangChain
- Proficiency in TypeScript, React, and web technologies
- Knowledge of C++ and strong computer science fundamentals
- Experience building production-grade RAG systems and evaluating AI models

**Gaps (Why it may not fit):**
- 5+ years of software engineering experience
- Experience with high-volume, distributed systems at scale
- Go or Rust programming languages
- Cloudflare Workers experience

#### 12. AI Engineer - FDE (Forward Deployed Engineer) at Databricks

- **Overall Score:** 4.0/10
- **Breakdown:** Skills: 8/10 | Experience: 2/10 | Education: 8/10 | Location: 2/10 | Salary: 5/10
- **Location:** Paris, France
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=8395601002

**Analysis:** The candidate possesses highly relevant technical skills in GenAI, RAG, and multi-agent systems, aligning well with the role's technical requirements. However, there is a significant mismatch in experience level, as the role requires 'extensive years of industry experience' while the candidate only has internship experience. Additionally, the candidate's location preferences (US/Canada) conflict with the job's European location requirements.

**Strengths (Why it fits):**
- Hands-on experience building production-grade RAG pipelines and multi-agent systems using LangChain and LangGraph.
- Experience with GenAI evaluation frameworks like RAGAS.
- Pursuing a graduate degree in a quantitative discipline (Master's in ECE).
- Experience deploying ML models using Docker, FastAPI, and cloud platforms (AWS, Azure).

**Gaps (Why it may not fit):**
- Extensive years of industry data science experience
- Databricks Intelligence Platform
- Apache Spark
- DSPy
- HuggingFace
- Pandas
- Scikit-learn

#### 13. Software Engineer, R2 Storage at Cloudflare

- **Overall Score:** 4.0/10
- **Breakdown:** Skills: 4/10 | Experience: 3/10 | Education: 8/10 | Location: 4/10 | Salary: 5/10
- **Location:** Hybrid
- **Source:** greenhouse

**Analysis:** The candidate has a strong academic background and impressive AI/ML projects, but lacks the specific distributed systems and storage experience required for the R2 Storage team. Additionally, the candidate's heavy focus on AI/ML does not align well with the core infrastructure nature of the role, and they lack professional experience in Rust or Go.

**Strengths (Why it fits):**
- Strong academic background in Computer Engineering
- Experience with backend development, Docker, and Redis
- Familiarity with TypeScript through project work

**Gaps (Why it may not fit):**
- Rust
- Go
- Distributed systems (consensus, replication)
- Distributed storage systems
- High-throughput, low-latency systems at scale

#### 14. AI Engineer - FDE (Forward Deployed Engineer) at Databricks

- **Overall Score:** 4.0/10
- **Breakdown:** Skills: 6/10 | Experience: 2/10 | Education: 9/10 | Location: 3/10 | Salary: 5/10
- **Location:** Remote - India
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=8099751002

**Analysis:** The candidate possesses highly relevant technical skills in GenAI, RAG, and LangChain, aligning well with the role's technical requirements. However, they fall significantly short of the 5+ years of required experience and prefer North America while the role is specifically designated for Remote - India.

**Strengths (Why it fits):**
- Hands-on experience building production-grade RAG pipelines and multi-agent systems using LangChain and LangGraph.
- Experience deploying machine learning and GenAI applications using Docker, FastAPI, and AWS/Azure.
- Relevant educational background with a Master's degree in Electrical and Computer Engineering.

**Gaps (Why it may not fit):**
- 5+ years of Data Science experience
- Customer-facing or consulting experience
- Databricks Intelligence Platform
- Apache Spark
- DSPy
- PyTorch
- pandas
- scikit-learn

#### 15. Software Engineer (Backend) at Cloudflare

- **Overall Score:** 4.0/10
- **Breakdown:** Skills: 4/10 | Experience: 1/10 | Education: 8/10 | Location: 5/10 | Salary: 5/10
- **Location:** In-Office
- **Source:** greenhouse

**Analysis:** The candidate has a strong academic background and relevant internship experience in AI/ML and backend development using Python and TypeScript. However, they fall significantly short of the 3-5+ years of required enterprise experience and lack specific required expertise in Model Context Protocol (MCP) servers and Infrastructure as Code.

**Strengths (Why it fits):**
- Strong programming skills in Python and TypeScript.
- Experience building backend services with FastAPI and REST APIs.
- Hands-on experience with LLMs, RAG pipelines, and AI integration.
- Containerization experience with Docker.

**Gaps (Why it may not fit):**
- 3-5+ years of enterprise experience
- Model Context Protocol (MCP) server development
- Infrastructure as Code (Terraform, Ansible, Chef)
- Go programming language
- Enterprise automation and configuration management

#### 16. Senior Software Engineer, AI Applications Tooling at Cloudflare

- **Overall Score:** 3.5/10
- **Breakdown:** Skills: 5/10 | Experience: 1/10 | Education: 8/10 | Location: 4/10 | Salary: 5/10
- **Location:** Hybrid
- **Source:** greenhouse

**Analysis:** While the candidate possesses strong foundational knowledge in LLMs, RAG, and agentic frameworks, they fall significantly short of the 5+ years of experience required for this senior role. Additionally, they lack the required expertise in edge/serverless architectures and large-scale distributed systems.

**Strengths (Why it fits):**
- Hands-on experience with modern AI agent patterns (LangGraph, LangChain) and RAG pipelines.
- Experience building automated AI evaluation pipelines using RAGAS.
- Proficiency in TypeScript and full-stack development.

**Gaps (Why it may not fit):**
- 5+ years of professional software engineering experience.
- Experience with Cloudflare platform or similar edge/serverless architectures.
- Large-scale distributed systems and edge-optimized model inference.
- Production-level AI observability and safety systems.

#### 17. Senior Software Engineer - Energy Markets (m/f/d) at 1KOMMA5˚

- **Overall Score:** 3.0/10
- **Breakdown:** Skills: 3/10 | Experience: 1/10 | Education: 7/10 | Location: 1/10 | Salary: 5/10
- **Location:** Berlin
- **Source:** arbeitnow

**Analysis:** The candidate is a recent graduate with internship experience, whereas the role requires a Senior Software Engineer with deep expertise in TypeScript backends and energy market integrations. Furthermore, there is a geographic mismatch as the role is based in Germany and the candidate prefers North America.

**Strengths (Why it fits):**
- Python and backend development experience (FastAPI, Node.js)
- Data pipeline and processing experience
- Strong academic background in Computer Engineering

**Gaps (Why it may not fit):**
- Senior-level engineering experience
- Energy service interfaces (smart meters, load balancing)
- GCP (Google Cloud Platform)
- CI/CD (GitHub Actions)
- Virtual power plant infrastructure

#### 18. Software Engineer, Game Development (f/m/d) at Iteration One GmbH

- **Overall Score:** 3.0/10
- **Breakdown:** Skills: 4/10 | Experience: 2/10 | Education: 8/10 | Location: 1/10 | Salary: 5/10
- **Location:** Karlsruhe
- **Source:** arbeitnow

**Analysis:** The candidate has a strong background in AI and software engineering, which aligns well with the company's heavy emphasis on AI tools. However, the candidate lacks the core technical requirements for the role (C# and Unity) and has location preferences (Remote/US/Canada) that fundamentally conflict with the job's on-site requirement in Germany.

**Strengths (Why it fits):**
- Strong AI/ML background including LLMs, RAG, and Computer Vision
- Solid academic foundation in software engineering and computer engineering
- Experience with mobile app development concepts and Android Studio

**Gaps (Why it may not fit):**
- C#
- Unity
- Live game operations
- Reactive programming (UniRx)
- Game performance optimization

#### 19. Senior Backend VPP Software Engineer - TypeScript (m/f/d) at 1KOMMA5˚

- **Overall Score:** 3.0/10
- **Breakdown:** Skills: 3/10 | Experience: 1/10 | Education: 7/10 | Location: 1/10 | Salary: 5/10
- **Location:** Berlin
- **Source:** arbeitnow

**Analysis:** The candidate is a junior-level engineer with a strong AI/ML background, while the role requires a Senior Backend Engineer with deep expertise in TypeScript, GCP, and Virtual Power Plant (VPP) infrastructure. Additionally, there is a geographic mismatch as the role is based in Germany, whereas the candidate prefers North America.

**Strengths (Why it fits):**
- Experience with Python in Machine Learning and Data Engineering contexts (listed as a bonus requirement)
- Backend development experience including Node.js, REST APIs, and databases
- Familiarity with cloud platforms and containerization (Docker)

**Gaps (Why it may not fit):**
- Senior-level backend experience
- Virtual Power Plant (VPP) and energy market domain knowledge
- NestJS
- Google Cloud Platform (GCP)
- Terraform
- Datadog

#### 20. Senior Software Engineer (Full Stack) at Cloudflare

- **Overall Score:** 3.0/10
- **Breakdown:** Skills: 7/10 | Experience: 1/10 | Education: 10/10 | Location: 1/10 | Salary: 5/10
- **Location:** In-Office
- **Source:** greenhouse

**Analysis:** While the candidate possesses strong educational credentials and relevant skills in AI and full-stack development, they are a massive mismatch for experience and location. The role requires 6+ years of senior-level experience and is based in-office in Bengaluru, whereas the candidate is a current student with only internship experience seeking roles in North America or remote.

**Strengths (Why it fits):**
- M.S. and B.S. in Computer Engineering
- Hands-on experience with modern AI infrastructure, including vector databases (Milvus, ChromaDB) and RAG pipelines
- Full-stack development proficiency using React, TypeScript, Python, and PostgreSQL

**Gaps (Why it may not fit):**
- 6+ years of professional experience
- Go
- Scala
- ClickHouse
- Senior-level system architecture and production operation experience

---
## Search: "Full-stack Developer"

**Jobs Scraped:** 34 unique
**Jobs Scored:** 20
**Sources:** greenhouse
**Duration:** 432.9s

**Average Score:** 4.1/10

### Match Results Overview

| # | Score | Company | Title | Location | Source | Apply Link |
|---|-------|---------|-------|----------|--------|------------|
| 1 | 8.0/10 | Figma | Software Engineer, Full Stack | San Francisco, CA • New York, NY • United States | greenhouse | [Apply](https://boards.greenhouse.io/figma/jobs/5691911004?gh_jid=5691911004) |
| 2 | 6.4/10 | Cloudflare | Fullstack Software Engineer | Hybrid | greenhouse | [Apply](https://boards.greenhouse.io/cloudflare/jobs/7542471?gh_jid=7542471) |
| 3 | 5.2/10 | Databricks | Software Engineer - Fullstack | Amsterdam, Netherlands | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8029677002) |
| 4 | 5.0/10 | Databricks | Senior Software Engineer - Fullstack | Seattle, Washington | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=6544403002) |
| 5 | 4.5/10 | Databricks | Senior Software Engineer - Fullstack | Mountain View, California; San Francisco, California | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=7898766002) |
| 6 | 4.5/10 | Databricks | Senior Software Engineer - Fullstack | Vancouver, Canada | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8099342002) |
| 7 | 4.5/10 | Databricks | Staff Software Engineer - Fullstack (NYC) | New York City, New York | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8384595002) |
| 8 | 4.0/10 | Databricks | Senior Software Engineer - Fullstack (NYC) | New York | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8211634002) |
| 9 | 4.0/10 | Databricks | Senior Software Engineer - Fullstack | Amsterdam, Netherlands | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8029679002) |
| 10 | 4.0/10 | Stripe | Full Stack Engineer, Link | Toronto, Remote in Canada | greenhouse | [Apply](https://stripe.com/jobs/search?gh_jid=6447175) |
| 11 | 4.0/10 | Databricks | Staff Fullstack Engineer | San Francisco, California | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=6704975002) |
| 12 | 4.0/10 | Databricks | Staff Software Engineer - Fullstack | Vancouver, Canada | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8099343002) |
| 13 | 3.5/10 | Cloudflare | Senior Software Engineer (Full Stack) | In-Office | greenhouse | [Apply](https://boards.greenhouse.io/cloudflare/jobs/7566807?gh_jid=7566807) |
| 14 | 3.5/10 | Databricks | Staff Fullstack Engineer, Agentic Applications | Mountain View, California | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8220836002) |
| 15 | 3.5/10 | Figma | Software Engineer, Fullstack - Figma Weave (Tel Aviv, Israel)  | Tel Aviv, Israel | greenhouse | [Apply](https://boards.greenhouse.io/figma/jobs/5692524004?gh_jid=5692524004) |
| 16 | 3.0/10 | Stripe | Staff Fullstack Engineer, Privy | NYC-Privy, US-Remote  | greenhouse | [Apply](https://stripe.com/jobs/search?gh_jid=7091959) |
| 17 | 3.0/10 | Databricks | Sr. Staff Fullstack Engineer, Agentic Applications | Mountain View, California | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8220902002) |
| 18 | 3.0/10 | Airbnb | Senior Fullstack Engineer, App Foundation | China | greenhouse | [Apply](https://careers.airbnb.com/positions/7551863?gh_jid=7551863) |
| 19 | 3.0/10 | Databricks | Staff Software Engineer - Fullstack | Bengaluru, India | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8037500002) |
| 20 | 2.0/10 | Databricks | Senior Software Engineer - Fullstack | Bengaluru, India | greenhouse | [Apply](https://databricks.com/company/careers/open-positions/job?gh_jid=8278343002) |

### Detailed Job Analysis

#### 1. Software Engineer, Full Stack at Figma

- **Overall Score:** 8.0/10
- **Breakdown:** Skills: 8/10 | Experience: 5/10 | Education: 9/10 | Location: 10/10 | Salary: 10/10
- **Location:** San Francisco, CA • New York, NY • United States
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/figma/jobs/5691911004?gh_jid=5691911004

**Analysis:** The candidate has a strong educational background and possesses many of the core technologies required by Figma, including React, TypeScript, Python, C++, and PostgreSQL. However, as a current Master's student with primarily internship experience, they may lack the extensive production experience typically expected for non-entry-level roles, though the posting mentions openness to varying seniority levels.

**Strengths (Why it fits):**
- Strong proficiency in modern full-stack technologies including React, TypeScript, Python, and PostgreSQL.
- Experience with C++, which is specifically highlighted as a nice-to-have for Figma's user-facing applications.
- Demonstrated ability to build and deploy end-to-end systems, such as the production-grade RAG pipeline.
- Solid educational foundation with a Master's degree in Electrical and Computer Engineering.

**Gaps (Why it may not fit):**
- Extensive experience maintaining large-scale full-stack applications in production
- WebAssembly (WASM)
- Ruby or Go (though Python and C++ compensate for this)

#### 2. Fullstack Software Engineer at Cloudflare

- **Overall Score:** 6.4/10
- **Breakdown:** Skills: 8/10 | Experience: 4/10 | Education: 9/10 | Location: 6/10 | Salary: 5/10
- **Location:** Hybrid
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/cloudflare/jobs/7542471?gh_jid=7542471

**Analysis:** The candidate possesses a strong educational background and relevant technical skills, particularly in TypeScript, React, PostgreSQL, and AI, which align well with the job's requirements and bonus points. However, the candidate's experience is limited to internships, which may not fully meet the expectations for a systems engineer responsible for designing, running, and scaling production services at Cloudflare's massive scale.

**Strengths (Why it fits):**
- Experience with TypeScript and React for UI frontends
- Strong background in AI/ML and LLMs, which is listed as a bonus point
- Experience with relational databases (PostgreSQL) and version control (Git)
- Solid educational foundation with degrees in Computer Engineering

**Gaps (Why it may not fit):**
- DNS and DNSSEC knowledge
- Cloudflare Workers & Pages
- Observability and monitoring tools (Kibana, Grafana, Prometheus)
- Gitlab CI
- Full-time production system operation and on-call experience

#### 3. Software Engineer - Fullstack at Databricks

- **Overall Score:** 5.2/10
- **Breakdown:** Skills: 7/10 | Experience: 3/10 | Education: 10/10 | Location: 1/10 | Salary: 5/10
- **Location:** Amsterdam, Netherlands
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=8029677002

**Analysis:** The candidate has a strong educational background and a tech stack that aligns well with the full-stack requirements, including React, Python, Node.js, and cloud technologies. However, the candidate lacks the required 2+ years of professional experience and large-scale distributed systems background, and the job location in Amsterdam conflicts with their preference for North America or remote work.

**Strengths (Why it fits):**
- Strong educational background with a BS and MS in Computer Engineering/ECE.
- Excellent match for the required tech stack, including React, Vue, Python, Java, Node.js, and SQL.
- Hands-on experience with cloud technologies (AWS, Azure) and containerization (Docker).

**Gaps (Why it may not fit):**
- 2+ years of professional frontend (HTML/CSS/JS) experience
- Experience operating large-scale distributed systems in a production environment
- Kubernetes

#### 4. Senior Software Engineer - Fullstack at Databricks

- **Overall Score:** 5.0/10
- **Breakdown:** Skills: 7/10 | Experience: 2/10 | Education: 8/10 | Location: 9/10 | Salary: 10/10
- **Location:** Seattle, Washington
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=6544403002

**Analysis:** The candidate possesses a strong foundation in the required technology stack, including React, Python, Node.js, and cloud technologies. However, as a current Master's student with only internship experience, they fall significantly short of the 5+ years of professional experience required for this Senior Software Engineer role.

**Strengths (Why it fits):**
- Strong alignment with the required tech stack (JavaScript, React, Python, Java, C++, SQL).
- Experience with cloud and containerization technologies (AWS, Azure, Docker).
- Solid educational background in Computer Engineering.

**Gaps (Why it may not fit):**
- 5+ years of professional software engineering experience.
- Experience developing large-scale distributed systems in a production environment.
- Deep front-end architecture experience at an enterprise scale.

#### 5. Senior Software Engineer - Fullstack at Databricks

- **Overall Score:** 4.5/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 8/10 | Location: 8/10 | Salary: 10/10
- **Location:** Mountain View, California; San Francisco, California
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=7898766002

**Analysis:** The candidate possesses a strong technical foundation in GenAI, RAG, and full-stack development that perfectly aligns with the team's product focus. However, as a current Master's student with only internship experience, they fall significantly short of the 5+ years of professional experience required for this Senior Software Engineer role.

**Strengths (Why it fits):**
- Strong alignment with the team's GenAI, RAG, and LLM focus
- Full-stack technical skills including React, Python, Java, and SQL
- Experience with cloud and containerization technologies (AWS, Docker)

**Gaps (Why it may not fit):**
- 5+ years of professional software engineering experience
- Experience developing large-scale distributed systems in a production environment
- Senior-level system architecture and mentorship experience

#### 6. Senior Software Engineer - Fullstack at Databricks

- **Overall Score:** 4.5/10
- **Breakdown:** Skills: 7/10 | Experience: 1/10 | Education: 9/10 | Location: 10/10 | Salary: 9/10
- **Location:** Vancouver, Canada
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=8099342002

**Analysis:** While the candidate possesses a strong educational background and matches many of the required technical skills like React, Python, and Docker, there is a significant gap in experience. The position is for a Senior Software Engineer requiring 5+ years of experience, whereas the candidate is a current Master's student with only internship-level experience.

**Strengths (Why it fits):**
- Proficient in required frontend and backend technologies including JavaScript, React, Python, Java, and SQL.
- Hands-on experience with cloud platforms (AWS, Azure) and containerization (Docker).
- Strong background in AI/ML, RAG, and LLMs, which aligns well with Databricks' AI-focused product teams.
- Location compatibility with the Vancouver office.

**Gaps (Why it may not fit):**
- 5+ years of professional full-stack software engineering experience.
- Experience developing and maintaining large-scale distributed systems.
- Kubernetes (k8s) experience.

#### 7. Staff Software Engineer - Fullstack (NYC) at Databricks

- **Overall Score:** 4.5/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 8/10 | Location: 8/10 | Salary: 9/10
- **Location:** New York City, New York
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=8384595002

**Analysis:** The candidate possesses a strong foundation in the required tech stack, including modern JavaScript frameworks, backend languages, and GenAI technologies which aligns well with the team's goals. However, the role is for a Staff Software Engineer requiring 10+ years of experience, whereas the candidate is a current Master's student with only internship experience, making them severely underqualified for this seniority level.

**Strengths (Why it fits):**
- Hands-on experience with GenAI, RAG, and LLMs, aligning perfectly with the team's GenAI-first approach
- Proficiency in required frontend technologies including HTML, CSS, JavaScript, React, and Vue
- Strong backend and database foundation with Python, Java, C++, Node.js, and SQL

**Gaps (Why it may not fit):**
- 10+ years of professional software engineering experience
- Experience building complex analytics visualizations at scale
- Staff-level architectural design and technical leadership experience

#### 8. Senior Software Engineer - Fullstack (NYC) at Databricks

- **Overall Score:** 4.0/10
- **Breakdown:** Skills: 7/10 | Experience: 1/10 | Education: 8/10 | Location: 7/10 | Salary: 10/10
- **Location:** New York
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=8211634002

**Analysis:** The candidate possesses a strong educational background and relevant technical skills in full-stack development and AI/ML, which aligns well with the team's GenAI focus. However, the role is for a Senior Software Engineer requiring 5+ years of experience, whereas the candidate only has internship-level experience, making them significantly underqualified for this specific position.

**Strengths (Why it fits):**
- Strong tech stack match including React, Vue, Python, Java, C++, Node.js, and SQL.
- Hands-on experience with GenAI, LLMs, and RAG pipelines, aligning with the team's GenAI-first approach.
- Solid educational background with a Master's degree in Electrical and Computer Engineering.

**Gaps (Why it may not fit):**
- 5+ years of professional software engineering experience.
- Experience building complex analytics visualizations.
- Proven track record of shipping high-quality code at high velocity in a large-scale production environment.

#### 9. Senior Software Engineer - Fullstack at Databricks

- **Overall Score:** 4.0/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 10/10 | Location: 1/10 | Salary: 5/10
- **Location:** Amsterdam, Netherlands
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=8029679002

**Analysis:** The candidate has a strong educational background and possesses many of the required technical skills, including React, Python, and cloud technologies. However, this is a Senior role requiring 5+ years of experience and large-scale distributed systems expertise, whereas the candidate only has internship experience. Additionally, the location (Amsterdam) does not align with the candidate's preferences.

**Strengths (Why it fits):**
- Strong educational background with a Master's in progress and a Bachelor's in Computer Engineering.
- Relevant tech stack including React, Vue, Python, Java, C++, SQL, AWS, and Docker.
- Experience building full-stack applications and AI/RAG pipelines.

**Gaps (Why it may not fit):**
- 5+ years of professional software engineering experience
- Experience operating large-scale distributed systems in production
- Deep understanding of front-end architecture at an enterprise level
- Kubernetes

#### 10. Full Stack Engineer, Link at Stripe

- **Overall Score:** 4.0/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 8/10 | Location: 10/10 | Salary: 5/10
- **Location:** Toronto, Remote in Canada
- **Source:** greenhouse
- **Apply URL:** https://stripe.com/jobs/search?gh_jid=6447175

**Analysis:** The candidate possesses strong full-stack technical skills and a solid educational background in computer engineering. However, they completely lack the strict minimum requirement of 2+ years of non-internship industry experience, making them fundamentally too junior for this mid-level role.

**Strengths (Why it fits):**
- Full-stack development capabilities (React, Node.js, FastAPI, PostgreSQL)
- Familiarity with preferred cloud and containerization technologies (AWS, Docker)
- Strong academic background in Computer Engineering with high GPA

**Gaps (Why it may not fit):**
- 2+ years of non-internship industry experience
- Mentoring experience
- Large-scale financial tracking systems
- gRPC
- GraphQL

#### 11. Staff Fullstack Engineer at Databricks

- **Overall Score:** 4.0/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 8/10 | Location: 7/10 | Salary: 10/10
- **Location:** San Francisco, California
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=6704975002

**Analysis:** The candidate possesses a solid technical foundation with relevant skills in React, JavaScript, and backend technologies. However, there is a significant mismatch in experience level, as the candidate is a current Master's student with only internship experience applying for a Staff/Senior level role that requires 5+ years of experience and proven leadership.

**Strengths (Why it fits):**
- Proficiency in modern JavaScript frameworks including React and Vue
- Experience with server-side web technologies such as Node.js, FastAPI, and PostgreSQL
- Strong academic background in Computer Engineering with high GPA

**Gaps (Why it may not fit):**
- 5+ years of professional software engineering experience
- Experience leading large multi-quarter engineering efforts
- Front-end architecture design at a massive scale
- Demonstrated business impact in a senior or staff capacity

#### 12. Staff Software Engineer - Fullstack at Databricks

- **Overall Score:** 4.0/10
- **Breakdown:** Skills: 5/10 | Experience: 1/10 | Education: 9/10 | Location: 10/10 | Salary: 10/10
- **Location:** Vancouver, Canada
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=8099343002

**Analysis:** The candidate possesses a strong educational background and familiarity with the required tech stack including React, Python, Docker, and AWS. However, the role is for a Staff Software Engineer requiring 10+ years of experience, whereas the candidate is a current Master's student with only internship experience, making them vastly underqualified for this seniority level.

**Strengths (Why it fits):**
- Strong academic background in Computer Engineering with high GPAs.
- Hands-on experience with modern full-stack and AI technologies including React, Python, FastAPI, Docker, RAG, and LLMs.
- Experience with cloud platforms such as AWS and Azure.
- Location match with ties to Vancouver as a UBC alumni.

**Gaps (Why it may not fit):**
- 10+ years of frontend development experience
- 10+ years of backend or server-side development experience
- Experience developing large-scale distributed systems in a production environment
- Kubernetes

#### 13. Senior Software Engineer (Full Stack) at Cloudflare

- **Overall Score:** 3.5/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 10/10 | Location: 1/10 | Salary: 3/10
- **Location:** In-Office
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/cloudflare/jobs/7566807?gh_jid=7566807

**Analysis:** The candidate has relevant technical skills in Python, React, and AI technologies, along with a matching educational background. However, they fall significantly short of the 6+ years of required experience and have conflicting location preferences (Bengaluru in-office vs. North America/Remote).

**Strengths (Why it fits):**
- Strong educational background with a B.A.Sc and ongoing M.Eng in relevant engineering fields.
- Relevant full-stack tech stack experience including Python, Java, React, TypeScript, and PostgreSQL.
- Hands-on experience with AI components, vector databases (Milvus, ChromaDB), and RAG pipelines, which is a highlighted requirement.

**Gaps (Why it may not fit):**
- 6+ years of professional experience
- Go
- Scala
- ClickHouse
- Mentorship experience
- System architecture at scale

#### 14. Staff Fullstack Engineer, Agentic Applications at Databricks

- **Overall Score:** 3.5/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 8/10 | Location: 7/10 | Salary: 10/10
- **Location:** Mountain View, California
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=8220836002

**Analysis:** The candidate possesses highly relevant technical skills in AI, LLMs, and full-stack development that align perfectly with the 'Agentic Applications' focus of the role. However, there is a massive gap in experience, as the position requires a Staff-level engineer with 12+ years of experience and 3+ years of leadership, whereas the candidate is a current Master's student with only internship experience.

**Strengths (Why it fits):**
- Hands-on experience building agentic applications using LangGraph and LangChain.
- Strong background in RAG systems, vector databases (ChromaDB, Milvus), and LLM integration.
- Full-stack cloud-native development skills including React, FastAPI, Docker, and PostgreSQL.
- Demonstrated ability to build end-to-end AI pipelines and evaluate them using frameworks like RAGAS.

**Gaps (Why it may not fit):**
- 12+ years of software engineering experience
- 3+ years of engineering leadership and team management
- Experience defining technical strategy and roadmaps at an enterprise level
- Mentoring junior engineers
- Staff-level system design and architecture for large-scale enterprise applications

#### 15. Software Engineer, Fullstack - Figma Weave (Tel Aviv, Israel)  at Figma

- **Overall Score:** 3.5/10
- **Breakdown:** Skills: 7/10 | Experience: 2/10 | Education: 8/10 | Location: 1/10 | Salary: 5/10
- **Location:** Tel Aviv, Israel
- **Source:** greenhouse
- **Apply URL:** https://boards.greenhouse.io/figma/jobs/5692524004?gh_jid=5692524004

**Analysis:** The candidate possesses strong foundational skills in full-stack development and AI, which align well with Figma's tech stack and AI initiatives. However, the candidate falls significantly short of the 5+ years of required experience and prefers North America, whereas the role is based in Tel Aviv.

**Strengths (Why it fits):**
- Experience with React, TypeScript, Node.js, and PostgreSQL
- Strong background in AI/ML, LLMs, and RAG, aligning with Figma's AI-native focus
- Academic background in Computer Graphics

**Gaps (Why it may not fit):**
- 5+ years of professional experience
- Ruby
- Go
- Rust
- WebAssembly

#### 16. Staff Fullstack Engineer, Privy at Stripe

- **Overall Score:** 3.0/10
- **Breakdown:** Skills: 4/10 | Experience: 1/10 | Education: 7/10 | Location: 10/10 | Salary: 8/10
- **Location:** NYC-Privy, US-Remote 
- **Source:** greenhouse
- **Apply URL:** https://stripe.com/jobs/search?gh_jid=7091959

**Analysis:** The candidate has a strong academic background and relevant full-stack skills including React and TypeScript. However, they are vastly underqualified for this Staff-level role, which requires 8+ years of experience compared to the candidate's internship-level background.

**Strengths (Why it fits):**
- Experience with React and TypeScript
- Full-stack development capabilities
- Has published academic work, aligning with a preferred qualification

**Gaps (Why it may not fit):**
- 8+ years of professional experience
- Next.js
- Web3/crypto experience
- Developer tooling experience
- Experience working closely with designers

#### 17. Sr. Staff Fullstack Engineer, Agentic Applications at Databricks

- **Overall Score:** 3.0/10
- **Breakdown:** Skills: 5/10 | Experience: 1/10 | Education: 8/10 | Location: 8/10 | Salary: 10/10
- **Location:** Mountain View, California
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=8220902002

**Analysis:** The candidate has highly relevant technical skills in AI, RAG, and full-stack development that align perfectly with the team's focus on agentic applications. However, the role is a Senior Staff position requiring 12+ years of experience and significant leadership, which the candidate completely lacks as a recent graduate.

**Strengths (Why it fits):**
- Direct experience building RAG systems and agentic pipelines using LangChain and LangGraph.
- Strong full-stack engineering capabilities including React, FastAPI, and Docker.
- Demonstrated passion for AI and data intelligence through academic research and projects.

**Gaps (Why it may not fit):**
- 12+ years of software engineering experience
- 3+ years of engineering leadership
- Technical strategy and roadmap definition
- Mentoring and team leadership

#### 18. Senior Fullstack Engineer, App Foundation at Airbnb

- **Overall Score:** 3.0/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 8/10 | Location: 3/10 | Salary: 5/10
- **Location:** China
- **Source:** greenhouse
- **Apply URL:** https://careers.airbnb.com/positions/7551863?gh_jid=7551863

**Analysis:** The candidate possesses relevant full-stack skills and a strong educational background, but falls significantly short of the 5+ years of experience required for this senior role. Furthermore, the candidate's location preferences (US/Canada) do not align well with the China-based requirement.

**Strengths (Why it fits):**
- Relevant full-stack technology stack including React, TypeScript, Java, and C++
- Strong educational background in Computer Engineering
- Demonstrated experience with testing practices and CI/CD pipelines
- Likely bilingual in English and Chinese based on education and internship history

**Gaps (Why it may not fit):**
- 5+ years of professional software development experience
- Experience designing and scaling high-traffic backend services
- Experience building foundational frameworks for large-scale applications

#### 19. Staff Software Engineer - Fullstack at Databricks

- **Overall Score:** 3.0/10
- **Breakdown:** Skills: 4/10 | Experience: 1/10 | Education: 7/10 | Location: 1/10 | Salary: 5/10
- **Location:** Bengaluru, India
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=8037500002

**Analysis:** The candidate is a current Master's student with internship experience, falling significantly short of the 10+ years of industry experience required for this Staff-level role. Furthermore, the job is located in Bengaluru, India, which conflicts with the candidate's geographic preferences.

**Strengths (Why it fits):**
- Full-stack development skills including React, Node.js, and FastAPI
- Experience with modern AI/ML technologies and data pipelines
- Strong educational background in Computer Engineering

**Gaps (Why it may not fit):**
- 10+ years of industry experience
- Experience leading large multi-quarter efforts
- Experience developing large-scale distributed systems from scratch
- Mentoring junior engineers
- SaaS platform or SOA experience at scale

#### 20. Senior Software Engineer - Fullstack at Databricks

- **Overall Score:** 2.0/10
- **Breakdown:** Skills: 4/10 | Experience: 1/10 | Education: 7/10 | Location: 1/10 | Salary: 5/10
- **Location:** Bengaluru, India
- **Source:** greenhouse
- **Apply URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=8278343002

**Analysis:** The candidate is a current Master's student with only internship experience, falling significantly short of the 6+ years of industry experience required for this senior-level role. Furthermore, the position is located in Bengaluru, India, which directly conflicts with the candidate's geographic preferences for Remote, US, or Canada.

**Strengths (Why it fits):**
- Full-stack development experience including React, FastAPI, and Node.js
- Strong academic background in Computer Engineering and Software Engineering
- Hands-on experience with AI/ML, specifically building RAG systems and working with LLMs

**Gaps (Why it may not fit):**
- 6+ years of industry experience
- Experience developing large-scale distributed systems from scratch
- Leading large multi-quarter efforts with demonstrated business impact
- Extensive experience working on a SaaS platform or with Service-Oriented Architectures at scale

---
## Pipeline Architecture

```
User Profile + Job Titles
        |
        v
+-----------------------------+
|   SCRAPING PHASE            |
|   Arbeitnow (5 pages)       |
|   Greenhouse (12 boards)    |
|   Lever (4 companies)       |
|   + Deduplication            |
+-------------+---------------+
              |
              v
+-----------------------------+
|   MATCHING PHASE            |
|   1. Gemini Embeddings      |
|   2. ChromaDB Vector Search |
|   3. FlashRank Reranking    |
|   4. Gemini LLM-as-Judge    |
+-------------+---------------+
              |
              v
+-----------------------------+
|   REPORT GENERATION         |
|   Detailed Markdown Report  |
|   with scores & analysis    |
+-----------------------------+
```

*Report generated by AI Job Application Agent E2E Pipeline Test*