# AI Job Application Agent — End-to-End Pipeline Test Report

**Generated:** 2026-02-27 21:51 UTC
**User:** Ruiqi Tian (Master of Engineering, U of Waterloo)
**Search Titles:** Software Engineer, AI Engineer, Full-stack Developer
**Target Locations:** Remote, United States, Canada
**Salary Range:** $100,000 - $200,000 USD
**Workplace:** remote, hybrid

---
## Executive Summary

| Metric | Value |
|--------|-------|
| Total Jobs Scraped | 34 |
| Total Jobs Scored | 20 |
| Search Queries | 3 |
| Scraping Sources | greenhouse |
| Scoring Model | Gemini (via Google AI) |
| Embedding Model | Gemini embedding-001 |
| Retrieval | ChromaDB (top-30) → FlashRank rerank (top-20) |

---
## Scraping Sources & Methodology

| Source | Type | Auth Required | Method |
|--------|------|---------------|--------|
| Arbeitnow | Public API | No | Full-text search with client-side keyword filtering across 5 pages |
| Greenhouse | Public Board API | No | Fetched ALL jobs from 12 boards, filtered by title keywords |
| Lever | Public Postings API | No | Fetched ALL postings from 4 companies, filtered by title keywords |

**Greenhouse Boards:** figma, cloudflare, stripe, datadog, airbnb, databricks, airtable, gusto, cockroachlabs, benchling, relativityspace, nianticlabs
**Lever Companies:** netflix, nerdwallet, rippling, samsara

---
## Search: "Full-stack Developer"

**Jobs Scraped:** 34 unique
**Jobs Scored:** 20
**Duration:** 432.9s

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
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Highlight the production-grade RAG system built during the Disanji Technology Institute internship, focusing on scalability and deployment.
- Discuss the architecture and full-stack implementation of the AI Agent-powered Resume Generator project, specifically the React/TypeScript frontend and FastAPI backend.
- Emphasize your experience with C++ and how it can be applied to Figma's performance-critical components.
- Explain your approach to balancing user experience craft with performance and architecture quality in your past projects.

**Job Description (preview):** &lt;div class=&quot;content-intro&quot;&gt;&lt;p&gt;Figma is growing our team of passionate creatives and builders on a mission to make design accessible to all. Figma’s platform helps teams bring ideas to life—whether you&#39;re brainstorming, creating a prototype, translating designs into code, or iterating with AI. From idea to product, Figma empowers teams to streamline workflows, move faster, and work together in real time from anywhere in the world. If you&#39;re excited to shape the futur...

#### 2. Fullstack Software Engineer at Cloudflare

- **Overall Score:** 6.4/10
- **Breakdown:** Skills: 8/10 | Experience: 4/10 | Education: 9/10 | Location: 6/10 | Salary: 5/10
- **Location:** Hybrid
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Highlight the full-stack architecture of the AI Agent project, specifically the React/TypeScript frontend and PostgreSQL backend.
- Discuss experience with Docker, deployment, and testing (80%+ coverage) to demonstrate readiness for systems engineering and operations.
- Emphasize the ability to learn quickly and deliver production-grade systems, as evidenced by the RAG system built during the Disanji Technology internship.
- Express a strong willingness to learn domain management, DNS, and Cloudflare's specific tech stack.

**Job Description (preview):** &lt;div class=&quot;content-intro&quot;&gt;&lt;div&gt;&lt;strong&gt;About Us&lt;/strong&gt;&lt;/div&gt; &lt;div&gt; &lt;p&gt;At Cloudflare, we are on a mission to help build a better Internet. Today the company runs one of the world’s largest networks that powers millions of websites and other Internet properties for customers ranging from individual bloggers to SMBs to Fortune 500 companies. Cloudflare protects and accelerates any Internet application online without adding hardware, installing ...

#### 3. Software Engineer - Fullstack at Databricks

- **Overall Score:** 5.2/10
- **Breakdown:** Skills: 7/10 | Experience: 3/10 | Education: 10/10 | Location: 1/10 | Salary: 5/10
- **Location:** Amsterdam, Netherlands
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Discuss the architecture and deployment of the production-grade RAG system built during the Disanji Technology Institute internship.
- Highlight full-stack development experience from the AI Agent-powered Resume Generator project, specifically using React, FastAPI, and PostgreSQL.
- Explain how academic and internship experiences have prepared you to work on complex, scalable systems despite lacking years of full-time experience.
- Clarify willingness to relocate to Amsterdam, Netherlands, given the stated location preferences.

**Job Description (preview):** &lt;p&gt;P-1320&lt;/p&gt; &lt;p&gt;At Databricks, we are passionate about enabling data teams to solve the world&#39;s toughest problems — from making the next mode of transportation a reality to accelerating the development of medical breakthroughs. We do this by building and running the world&#39;s best data and AI infrastructure platform so our customers can use deep data insights to improve their business. Founded by engineers — and customer obsessed — we leap at every opportunity to solve t...

#### 4. Senior Software Engineer - Fullstack at Databricks

- **Overall Score:** 5.0/10
- **Breakdown:** Skills: 7/10 | Experience: 2/10 | Education: 8/10 | Location: 9/10 | Salary: 10/10
- **Location:** Seattle, Washington
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Highlight complex architectural decisions made during the RAG system internship and AI Agent project.
- Discuss experience with Docker, AWS, and Azure to demonstrate readiness for cloud-native development.
- Emphasize ability to learn quickly and handle full-stack responsibilities to mitigate the lack of years of experience.

**Job Description (preview):** &lt;p&gt;P-951&lt;/p&gt; &lt;p&gt;At Databricks, we are passionate about enabling data teams to solve the world&#39;s toughest problems — from making the next mode of transportation a reality to accelerating the development of medical breakthroughs. We do this by building and running the world&#39;s best Data Intelligence Platform so our customers can use deep data insights to improve their business. Founded by engineers — and customer obsessed — we leap at every opportunity to tackle technical ...

#### 5. Senior Software Engineer - Fullstack at Databricks

- **Overall Score:** 4.5/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 8/10 | Location: 8/10 | Salary: 10/10
- **Location:** Mountain View, California; San Francisco, California
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Highlight the production-grade RAG system built during the Disanji Technology Institute internship
- Discuss the architecture of the AI Agent-powered LangGraph pipeline and how it handles scale and evaluation
- Emphasize fast learning capabilities and deep understanding of GenAI observability to compensate for the lack of years of experience

**Job Description (preview):** &lt;p&gt;P-160&lt;/p&gt; &lt;p&gt;&lt;strong&gt;Who We Are&lt;/strong&gt;&lt;/p&gt; &lt;p&gt;Our GenAI observability and quality product provides advanced monitoring and insights for GenAI systems, giving customers real-time visibility into their system&#39;s performance, along with a suite of tools to improve the quality of the GenAI systems. With features like real-time alerts, detailed logging, and anomaly detection, customers can quickly identify and fix issues that affect the quality of the...

#### 6. Senior Software Engineer - Fullstack at Databricks

- **Overall Score:** 4.5/10
- **Breakdown:** Skills: 7/10 | Experience: 1/10 | Education: 9/10 | Location: 10/10 | Salary: 9/10
- **Location:** Vancouver, Canada
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Discuss the architecture and deployment of the production-grade RAG system built during the Disanji Technology Institute internship.
- Highlight the full-stack AI Agent project, focusing on the integration of React, FastAPI, and PostgreSQL.
- Explain how academic background and internship experiences have prepared them to quickly ramp up on large-scale distributed systems.
- Express strong interest in the Databricks Apps and AI/BI teams, leveraging existing knowledge in LLMs and full-stack development.

**Job Description (preview):** &lt;p&gt;Databricks is on a mission to simplify and democratize data and AI — from making the next mode of transportation a reality to accelerating the development of medical breakthroughs. We do this by building and running the world&#39;s best data and AI infrastructure platform so our customers can use deep data insights to improve their business. Founded by engineers — and customer obsessed — we leap at every opportunity to solve technical challenges, from designing next-gen UI/UX for interf...

#### 7. Staff Software Engineer - Fullstack (NYC) at Databricks

- **Overall Score:** 4.5/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 8/10 | Location: 8/10 | Salary: 9/10
- **Location:** New York City, New York
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Highlight the end-to-end RAG pipeline and GenAI projects, as the Databricks team is building vertical AI applications
- Discuss full-stack projects involving React and backend APIs to demonstrate the ability to build UI-first applications
- Acknowledge the experience gap but emphasize rapid learning, high velocity, and recent academic and internship achievements in AI

**Job Description (preview):** &lt;p&gt;P-1980&lt;br&gt;&lt;br&gt;At Databricks, we are passionate about enabling data teams to solve the world&#39;s toughest problems — from making the next mode of transportation a reality to accelerating the development of medical breakthroughs. We do this by building and running the world&#39;s best Data Intelligence Platform so our customers can use deep data insights to improve their business. Founded by engineers — and customer obsessed — we leap at every opportunity to tackle technical...

#### 8. Senior Software Engineer - Fullstack (NYC) at Databricks

- **Overall Score:** 4.0/10
- **Breakdown:** Skills: 7/10 | Experience: 1/10 | Education: 8/10 | Location: 7/10 | Salary: 10/10
- **Location:** New York
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Highlight experience building end-to-end RAG pipelines and AI agents, as the role involves creating interfaces for GenAI agents.
- Discuss full-stack projects, specifically focusing on React/TypeScript and backend integration.
- Emphasize ability to learn quickly and adapt to complex data workflows to compensate for the lack of senior-level experience.

**Job Description (preview):** &lt;p&gt;P-1473&lt;/p&gt; &lt;p&gt;At Databricks, we are passionate about enabling data teams to solve the world&#39;s toughest problems — from making the next mode of transportation a reality to accelerating the development of medical breakthroughs. We do this by building and running the world&#39;s best Data Intelligence Platform so our customers can use deep data insights to improve their business. Founded by engineers — and customer obsessed — we leap at every opportunity to tackle technical...

#### 9. Senior Software Engineer - Fullstack at Databricks

- **Overall Score:** 4.0/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 10/10 | Location: 1/10 | Salary: 5/10
- **Location:** Amsterdam, Netherlands
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Highlight full-stack projects, specifically the AI Agent-powered Resume Generator using React, FastAPI, and Docker.
- Discuss experience with cloud technologies and deploying applications via Docker.
- Emphasize quick learning ability and strong academic foundation to bridge the experience gap.
- Clarify willingness to relocate to Amsterdam or work remotely if the company allows.

**Job Description (preview):** &lt;p&gt;P-1321&lt;/p&gt; &lt;p&gt;At Databricks, we are passionate about enabling data teams to solve the world&#39;s toughest problems — from making the next mode of transportation a reality to accelerating the development of medical breakthroughs. We do this by building and running the world&#39;s best data and AI infrastructure platform so our customers can use deep data insights to improve their business. Founded by engineers — and customer obsessed — we leap at every opportunity to solve t...

#### 10. Full Stack Engineer, Link at Stripe

- **Overall Score:** 4.0/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 8/10 | Location: 10/10 | Salary: 5/10
- **Location:** Toronto, Remote in Canada
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Highlight end-to-end project ownership to demonstrate the required autonomy and entrepreneurial mindset.
- Discuss experience deploying applications using Docker and AWS to align with preferred qualifications.
- Emphasize rapid learning capabilities to compensate for the lack of formal years of experience.

**Job Description (preview):** &lt;h2&gt;Who we are&lt;/h2&gt; &lt;h3&gt;About the Organization&amp;nbsp;&lt;/h3&gt; &lt;p&gt;Link is a digital wallet designed for effortless and secure online payments and digital transactions. With Link, consumers enjoy convenience and peace of mind: it works on any device or browser, is backed by the highest security mechanisms, offers purchase protections on eligible items, and ensures seamless and quick payments. Across the Link Engineering org, we focus on building delightful payment exp...

#### 11. Staff Fullstack Engineer at Databricks

- **Overall Score:** 4.0/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 8/10 | Location: 7/10 | Salary: 10/10
- **Location:** San Francisco, California
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Discuss the full-stack architecture and implementation of the AI Agent-powered Resume Generator project.
- Explain your approach to building and deploying the production-grade RAG system during your internship.
- Highlight your rapid learning capabilities and strong academic performance to help mitigate the lack of professional years of experience.

**Job Description (preview):** &lt;p&gt;P-925&lt;/p&gt; &lt;p&gt;At Databricks, we are passionate about enabling data teams to solve the world&#39;s toughest problems — from making the next mode of transportation a reality to accelerating the development of medical breakthroughs. We do this by building and running the world&#39;s best data and AI infrastructure platform so our customers can use deep data insights to improve their business. Founded by engineers — and customer obsessed — we leap at every opportunity to tackle t...

#### 12. Staff Software Engineer - Fullstack at Databricks

- **Overall Score:** 4.0/10
- **Breakdown:** Skills: 5/10 | Experience: 1/10 | Education: 9/10 | Location: 10/10 | Salary: 10/10
- **Location:** Vancouver, Canada
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Highlight complex architectural decisions made during internships, such as the end-to-end RAG pipeline.
- Discuss full-stack projects, specifically the AI Agent-powered Resume Generator using React and FastAPI.
- Emphasize fast learning ability and deep understanding of AI and BI concepts which align with Databricks' product focus.
- Acknowledge the gap in years of experience but demonstrate maturity, system design knowledge, and readiness to tackle complex distributed systems challenges.

**Job Description (preview):** &lt;p&gt;Databricks is on a mission to simplify and democratize data and AI — from making the next mode of transportation a reality to accelerating the development of medical breakthroughs. We do this by building and running the world&#39;s best data and AI infrastructure platform so our customers can use deep data insights to improve their business. Founded by engineers — and customer obsessed — we leap at every opportunity to solve technical challenges, from designing next-gen UI/UX for interf...

#### 13. Senior Software Engineer (Full Stack) at Cloudflare

- **Overall Score:** 3.5/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 10/10 | Location: 1/10 | Salary: 3/10
- **Location:** In-Office
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Detail the architecture and impact of the production-grade RAG system built during the Disanji Technology Institute internship.
- Discuss experience building full-stack applications with React and Python/FastAPI.
- Explain strategies for quickly learning new technologies like Go or ClickHouse to contribute to the team's multi-language stack.

**Job Description (preview):** &lt;div class=&quot;content-intro&quot;&gt;&lt;div&gt;&lt;strong&gt;About Us&lt;/strong&gt;&lt;/div&gt; &lt;div&gt; &lt;p&gt;At Cloudflare, we are on a mission to help build a better Internet. Today the company runs one of the world’s largest networks that powers millions of websites and other Internet properties for customers ranging from individual bloggers to SMBs to Fortune 500 companies. Cloudflare protects and accelerates any Internet application online without adding hardware, installing ...

#### 14. Staff Fullstack Engineer, Agentic Applications at Databricks

- **Overall Score:** 3.5/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 8/10 | Location: 7/10 | Salary: 10/10
- **Location:** Mountain View, California
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Highlight the architectural complexity of the 4-agent LangGraph pipeline built for the resume generator project.
- Discuss the measurable impact of the RAG system built during the Disanji Technology Institute internship (e.g., 35% retrieval precision improvement).
- Acknowledge the significant experience gap but emphasize a deep, cutting-edge understanding of the data intelligence and AI agent space.
- Explain your approach to ensuring engineering quality, such as achieving 80%+ test coverage and building automated evaluation pipelines.

**Job Description (preview):** &lt;p&gt;The Enterprise Applications team at Databricks is on an ambitious journey to transform how we run the business.&amp;nbsp; Our mission is to build resilient, in-house platforms and AI-powered capabilities that provide a genuine competitive advantage, powering our next doubling in size and revenue.&lt;/p&gt; &lt;p&gt;As a Staff Software Engineer on the Enterprise Applications team, you will play a critical role delivering end-to-end applications that power our business and empower our emp...

#### 15. Software Engineer, Fullstack - Figma Weave (Tel Aviv, Israel)  at Figma

- **Overall Score:** 3.5/10
- **Breakdown:** Skills: 7/10 | Experience: 2/10 | Education: 8/10 | Location: 1/10 | Salary: 5/10
- **Location:** Tel Aviv, Israel
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Highlight full-stack projects using React, TypeScript, and PostgreSQL.
- Discuss academic and practical experience with Computer Graphics and how it applies to design tools.
- Emphasize recent work building AI/RAG pipelines and how that can contribute to Figma's AI-native platform.

**Job Description (preview):** &lt;div class=&quot;content-intro&quot;&gt;&lt;p&gt;Figma is growing our team of passionate creatives and builders on a mission to make design accessible to all. Figma’s platform helps teams bring ideas to life—whether you&#39;re brainstorming, creating a prototype, translating designs into code, or iterating with AI. From idea to product, Figma empowers teams to streamline workflows, move faster, and work together in real time from anywhere in the world. If you&#39;re excited to shape the futur...

#### 16. Staff Fullstack Engineer, Privy at Stripe

- **Overall Score:** 3.0/10
- **Breakdown:** Skills: 4/10 | Experience: 1/10 | Education: 7/10 | Location: 10/10 | Salary: 8/10
- **Location:** NYC-Privy, US-Remote 
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Discuss the architecture and full-stack implementation of the AI Agent Resume Generator using React and TypeScript.
- Highlight the ACM MM '23 publication to demonstrate ability to research and publish complex technical work.
- Explain how experience building end-to-end pipelines translates to building developer tools.

**Job Description (preview):** &lt;h2&gt;&lt;strong&gt;Who we are&lt;/strong&gt;&lt;/h2&gt; &lt;h3&gt;&lt;strong&gt;About Privy&lt;/strong&gt;&lt;/h3&gt; &lt;p&gt;Our mission is to make privacy and user ownership the default online. We build simple, flexible developer tooling that make it easy to build products that put users first. By leveraging modern cryptography, we shift the status quo around digital ownership and protect the accounts and assets of millions of users.&lt;/p&gt; &lt;p&gt;Engineering at Privy is not just ab...

#### 17. Sr. Staff Fullstack Engineer, Agentic Applications at Databricks

- **Overall Score:** 3.0/10
- **Breakdown:** Skills: 5/10 | Experience: 1/10 | Education: 8/10 | Location: 8/10 | Salary: 10/10
- **Location:** Mountain View, California
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Discuss the architectural decisions made when building the 4-agent LangGraph pipeline.
- Explain the evaluation metrics and improvements achieved in the production-grade RAG system.
- Acknowledge the experience gap but emphasize rapid learning ability and deep understanding of modern AI application stacks.

**Job Description (preview):** &lt;p&gt;The Enterprise Applications team at Databricks is on an ambitious journey to transform how we run the business.&amp;nbsp; Our mission is to build resilient, in-house platforms and AI-powered capabilities that provide a genuine competitive advantage, powering our next doubling in size and revenue.&lt;/p&gt; &lt;p&gt;As a Senior Staff Software Engineer on the Enterprise Applications team, you will play a critical role delivering end-to-end applications that power our business and empower ...

#### 18. Senior Fullstack Engineer, App Foundation at Airbnb

- **Overall Score:** 3.0/10
- **Breakdown:** Skills: 6/10 | Experience: 1/10 | Education: 8/10 | Location: 3/10 | Salary: 5/10
- **Location:** China
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Discuss the architectural decisions and full-stack implementation of the AI Agent-powered project.
- Explain your approach to testing and maintaining high code quality.
- Clarify your current location, work authorization, and willingness to work in China or remotely for a China-based team.

**Job Description (preview):** &lt;div class=&quot;content-intro&quot;&gt;&lt;p&gt;&lt;span style=&quot;font-family: helvetica, arial, sans-serif; font-size: 12pt;&quot;&gt;Airbnb was born in 2007 when two hosts welcomed three guests to their San Francisco home, and has since grown to over 5 million hosts who have welcomed over 2 billion guest arrivals in almost every country across the globe. Every day, hosts offer unique stays and experiences that make it possible for guests to connect with communities in a more authentic w...

#### 19. Staff Software Engineer - Fullstack at Databricks

- **Overall Score:** 3.0/10
- **Breakdown:** Skills: 4/10 | Experience: 1/10 | Education: 7/10 | Location: 1/10 | Salary: 5/10
- **Location:** Bengaluru, India
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Highlight full-stack projects and experience with React and backend APIs
- Discuss experience building data pipelines and RAG systems
- Explain ability to learn quickly and adapt to complex technical challenges

**Job Description (preview):** &lt;p&gt;P- 1430&lt;/p&gt; &lt;p&gt;At Databricks, we are passionate about enabling data teams to solve the world&#39;s toughest problems — from making the next mode of transportation a reality to accelerating the development of medical breakthroughs. We do this by building and running the world&#39;s best data and AI infrastructure platform so our customers can use deep data insights to improve their business. Founded by engineers — and customer obsessed — we leap at every opportunity to tackle...

#### 20. Senior Software Engineer - Fullstack at Databricks

- **Overall Score:** 2.0/10
- **Breakdown:** Skills: 4/10 | Experience: 1/10 | Education: 7/10 | Location: 1/10 | Salary: 5/10
- **Location:** Bengaluru, India
- **Employment Type:** Not specified
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

**Interview Talking Points:**
- Discuss the architecture and technical challenges of the production-grade RAG system built during the Disanji Technology Institute internship.
- Highlight full-stack capabilities and testing practices demonstrated in the AI Agent-powered Resume Generator project.
- Explain how academic knowledge in DevOps and performance testing can be applied to building robust, scalable products.

**Job Description (preview):** &lt;p&gt;P- 1430&lt;/p&gt; &lt;p&gt;At Databricks, we are passionate about enabling data teams to solve the world&#39;s toughest problems — from making the next mode of transportation a reality to accelerating the development of medical breakthroughs. We do this by building and running the world&#39;s best data and AI infrastructure platform so our customers can use deep data insights to improve their business. Founded by engineers — and customer obsessed — we leap at every opportunity to tackle...

---
## Pipeline Architecture

```
User Profile + Job Titles
        │
        ▼
┌─────────────────────────────┐
│   SCRAPING PHASE            │
│   Arbeitnow (5 pages)       │
│   Greenhouse (12 boards)     │
│   Lever (7 companies)        │
│   + Deduplication            │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│   MATCHING PHASE            │
│   1. Gemini Embeddings      │
│   2. ChromaDB Vector Search  │
│   3. FlashRank Reranking     │
│   4. Gemini LLM-as-Judge     │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│   REPORT GENERATION         │
│   Detailed Markdown Report   │
│   with scores & analysis     │
└─────────────────────────────┘
```

*Report generated by AI Job Application Agent E2E Pipeline Test*