"""
A scraper for UN DESA Publications (https://sdgs.un.org/publications).
"""

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..entities import Card, Settings
from ._base import BaseScraper


class Scraper(BaseScraper):
    """
    Scraper for UN DESA Publications (https://sdgs.un.org/publications).
    """

    def __init__(self, settings: Settings | None = None):
        super().__init__(url_base="https://sdgs.un.org", settings=settings)

    async def collect_cards(self, page: int = 0) -> None:
        url = f"{self.url_base}/publications"
        params = {"page": page}
        if (soup := await self.get_soup(url, params)) is None:
            return
        cards = soup.find_all("div", {"class": "card-custom"})
        urls = [card.find("a").get("href") for card in cards]
        urls = [self.url_base + url for url in urls]
        cards = [Card(url=url) for url in urls]
        self.cards.update(cards)

    @staticmethod
    def _parse_title(soup: BeautifulSoup) -> str | None:
        if h1 := soup.find("h1"):
            title = h1.text.strip()
            return title
        return None

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
        return None

    @staticmethod
    def _parse_urls(soup: BeautifulSoup) -> set[str]:
        content = soup.find("div", {"id": "myTabContent"})
        anchors = content.find_all("a", {"class": "document-name"})
        base = "https://sdgs.un.org"
        urls = {
            urljoin(base, href)
            for a in anchors
            if (href := a.get("href", "")).endswith(".pdf")
        }
        return urls
