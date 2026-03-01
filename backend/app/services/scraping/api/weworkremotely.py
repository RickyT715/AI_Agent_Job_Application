"""WeWorkRemotely RSS feed scraper.

Parses RSS feeds from WeWorkRemotely job categories.
No authentication required.
"""

import logging
import xml.etree.ElementTree as ET

import httpx

from app.schemas.matching import JobPosting
from app.services.scraping.base import BaseScraper, ScrapingResult

logger = logging.getLogger(__name__)

# RSS feed URLs by category
CATEGORY_FEEDS: dict[str, str] = {
    "programming": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "devops": "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "design": "https://weworkremotely.com/categories/remote-design-jobs.rss",
    "full-stack": "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
}


class WeWorkRemotelyScraper(BaseScraper):
    """Scraper for WeWorkRemotely RSS feeds."""

    SOURCE = "weworkremotely"

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        categories: list[str] | None = None,
    ) -> None:
        super().__init__(client)
        self._categories = categories or list(CATEGORY_FEEDS.keys())

    async def scrape(self, query: str = "Software Engineer", **kwargs) -> ScrapingResult:
        """Fetch and parse RSS feeds from WeWorkRemotely.

        Args:
            query: Job search query (used for client-side filtering).
            **kwargs: Optional: categories (list of category slugs).
        """
        result = ScrapingResult(source=self.SOURCE)
        client = await self._get_client()
        query_lower = query.lower()
        categories = kwargs.get("categories", self._categories)

        for category in categories:
            feed_url = CATEGORY_FEEDS.get(category)
            if not feed_url:
                continue

            try:
                response = await client.get(feed_url)
                response.raise_for_status()

                items = self._parse_rss(response.text)
                result.total_found += len(items)

                for raw in items:
                    title = (raw.get("title") or "").lower()
                    description = (raw.get("description") or "").lower()

                    if query_lower in title or query_lower in description:
                        raw["category"] = category
                        posting = self.normalize(raw)
                        if posting:
                            result.jobs.append(posting)

            except httpx.HTTPStatusError as e:
                logger.error(f"WeWorkRemotely feed error ({category}): {e}")
                result.errors.append(f"HTTP {e.response.status_code} for {category}")
            except httpx.HTTPError as e:
                logger.error(f"WeWorkRemotely request failed ({category}): {e}")
                result.errors.append(f"Request failed for {category}")
            except ET.ParseError as e:
                logger.error(f"WeWorkRemotely XML parse error ({category}): {e}")
                result.errors.append(f"XML parse error for {category}")

        return result

    def _parse_rss(self, xml_text: str) -> list[dict]:
        """Parse RSS XML into list of item dicts."""
        items: list[dict] = []
        root = ET.fromstring(xml_text)

        for item in root.iter("item"):
            entry: dict[str, str] = {}
            for child in item:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                entry[tag] = child.text or ""
            items.append(entry)

        return items

    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Convert RSS item to JobPosting."""
        try:
            title = raw_data.get("title", "")
            if not title:
                return None

            link = raw_data.get("link", "")
            guid = raw_data.get("guid", link)
            if not guid:
                return None

            # WWR titles often include company: "Company Name: Job Title"
            company = "Unknown"
            job_title = title
            if ": " in title:
                parts = title.split(": ", 1)
                company = parts[0].strip()
                job_title = parts[1].strip()

            description = raw_data.get("description", "")
            category = raw_data.get("category", "")

            return JobPosting(
                external_id=guid,
                source=self.SOURCE,
                title=job_title,
                company=company,
                location="Remote",
                workplace_type="remote",
                description=description,
                requirements=category if category else None,
                apply_url=link,
                raw_data=raw_data,
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(f"Failed to normalize WeWorkRemotely job: {e}")
            return None
