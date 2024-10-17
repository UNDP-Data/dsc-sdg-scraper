"""
A scraper for UN DESA Publications (https://sdgs.un.org/publications).
"""

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ._base import BaseScraper


class Scraper(BaseScraper):
    """
    Scraper for UN DESA Publications (https://sdgs.un.org/publications).
    """

    def __init__(
        self,
        folder_path: str = None,
        **kwargs,
    ):
        super().__init__(
            url_base="https://sdgs.un.org",
            folder_path=folder_path,
            **kwargs,
        )

    async def parse_listing(self, page: int = 0) -> None:
        url = f"{self.url_base}/publications"
        response = await self.client.get(url, params={"page": page})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, features="lxml")
        cards = soup.find_all("div", {"class": "card-custom"})
        urls = [card.find("a").get("href") for card in cards]
        urls = [self.url_base + url for url in urls]
        self._urls.update(urls)

    @staticmethod
    def _parse_title(soup: BeautifulSoup) -> str | None:
        if h1 := soup.find("h1"):
            title = h1.text.strip()
            return title

    @staticmethod
    def _parse_type(soup: BeautifulSoup) -> str | None:
        return None

    @staticmethod
    def _parse_year(soup: BeautifulSoup) -> int | None:
        date = soup.find("span", {"class": "date"})
        try:
            date = re.search(r"(\d{4})", date.text).group()
            year = int(date)
        except (AttributeError, TypeError, ValueError):
            year = None
        return year

    @staticmethod
    def _parse_labels(soup: BeautifulSoup) -> list[int] | None:
        if goals := soup.find("div", {"class": "goals-content"}):
            labels = sorted(int(a.text) for a in goals.find_all("span"))
            return labels

    @staticmethod
    def _parse_urls(soup: BeautifulSoup) -> list[str]:
        content = soup.find("div", {"id": "myTabContent"})
        anchors = content.find_all("a", {"class": "document-name"})
        base = "https://sdgs.un.org"
        urls = [
            urljoin(base, href)
            for a in anchors
            if (href := a.get("href", "")).endswith(".pdf")
        ]
        return urls
