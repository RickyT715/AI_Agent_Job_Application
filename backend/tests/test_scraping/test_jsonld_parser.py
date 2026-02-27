"""Tests for JSON-LD extraction from HTML pages."""

from app.services.scraping.browser.generic import extract_jsonld_jobs


class TestExtractJsonldJobs:
    """Tests for JSON-LD job posting extraction."""

    def test_extracts_job_posting(self, page_with_jsonld):
        jobs = extract_jsonld_jobs(page_with_jsonld)
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Machine Learning Engineer"

    def test_extracts_hiring_org(self, page_with_jsonld):
        jobs = extract_jsonld_jobs(page_with_jsonld)
        org = jobs[0]["hiringOrganization"]
        assert org["name"] == "AI Corp"

    def test_extracts_salary(self, page_with_jsonld):
        jobs = extract_jsonld_jobs(page_with_jsonld)
        salary = jobs[0]["baseSalary"]["value"]
        assert salary["minValue"] == 150000
        assert salary["maxValue"] == 220000

    def test_no_jsonld_returns_empty(self, page_without_jsonld):
        jobs = extract_jsonld_jobs(page_without_jsonld)
        assert jobs == []

    def test_handles_multiple_script_tags(self):
        html = '''<html><head>
        <script type="application/ld+json">
        {"@type": "Organization", "name": "NotAJob"}
        </script>
        <script type="application/ld+json">
        {"@type": "JobPosting", "title": "Engineer", "description": "A job."}
        </script>
        </head><body></body></html>'''
        jobs = extract_jsonld_jobs(html)
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Engineer"

    def test_handles_graph_array(self):
        html = '''<html><head>
        <script type="application/ld+json">
        {"@graph": [
            {"@type": "WebPage", "name": "Careers"},
            {"@type": "JobPosting", "title": "Designer", "description": "Design things."}
        ]}
        </script>
        </head><body></body></html>'''
        jobs = extract_jsonld_jobs(html)
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Designer"

    def test_handles_invalid_json(self):
        html = '''<html><head>
        <script type="application/ld+json">
        {invalid json content here}
        </script>
        </head><body></body></html>'''
        jobs = extract_jsonld_jobs(html)
        assert jobs == []

    def test_handles_empty_html(self):
        jobs = extract_jsonld_jobs("")
        assert jobs == []
