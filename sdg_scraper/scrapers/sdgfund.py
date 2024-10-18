"""
A scraper for SDG Fund Library (https://www.sdgfund.org/library).
As of 2023, the library is archived but still accessible.
"""

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..entities import Card, Settings
from ._base import BaseScraper


class Scraper(BaseScraper):
    """
    Scraper for SDG Fund Library (https://www.sdgfund.org/library).
    """

    def __init__(self, settings: Settings | None = None):
        super().__init__(url_base="https://www.sdgfund.org/", settings=settings)

    async def collect_cards(self, page: int = 1) -> None:
        url = f"{self.url_base}/library"
        params = {"submit": "search", "page": page}
        if (soup := await self.get_soup(url, params)) is None:
            return
        cards = soup.find_all("div", {"class": "row-publication-teaser"})
        urls = [urljoin(self.url_base, card.find("a").get("href")) for card in cards]
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
        date = soup.find("span", {"class": "date-display-single"})
        try:
            date = date.text.strip()
            year = int(date)
        except (AttributeError, TypeError, ValueError):
            year = None
        return year

    @staticmethod
    def _parse_labels(soup: BeautifulSoup) -> list[int] | None:
        goals = [
            a.get("title") for a in soup.find_all("a", {"class": "sdg-icon-small"})
        ]
        if goals is None:
            return None
        labels = re.findall(pattern=r"\d+", string="".join(goals))
        labels = sorted(map(int, labels))
        return labels

    @staticmethod
    def _parse_urls(soup: BeautifulSoup) -> set[str]:
        anchors = soup.find_all("a", {"class": "library-link"})
        urls = {a.get("href") for a in anchors if a.get("href", "").endswith(".pdf")}
        return urls
