"""
A scraper for UNDP Publications (https://www.undp.org/publications).
"""

import re
from datetime import datetime

from bs4 import BeautifulSoup

from ._base import BaseScraper


class Scraper(BaseScraper):
    """
    Scraper for UNDP Publications (https://www.undp.org/publications).
    """

    def __init__(
        self,
        folder_path: str = None,
        **kwargs,
    ):
        super().__init__(
            url_base="https://www.undp.org",
            folder_path=folder_path,
            **kwargs,
        )

    async def parse_listing(self, page: int = 0) -> None:
        url = f"{self.url_base}/publications"
        response = await self.client.get(url, params={"page": page})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, features="lxml")
        cards = soup.find_all("div", {"class": "content-card"})
        urls = [card.find("a").get("href") for card in cards]
        self._urls.update(urls)

    @staticmethod
    def _parse_title(soup: BeautifulSoup) -> str | None:
        if title := soup.find("h2", {"class": "coh-heading"}):
            title = title.text.strip()
        return title

    @staticmethod
    def _parse_type(soup: BeautifulSoup) -> str | None:
        metadata = Scraper.__parse_metadata(soup)
        if kind := metadata.get("type"):
            kind = "|".join(kind)
        return kind

    @staticmethod
    def _parse_year(soup: BeautifulSoup) -> int | None:
        if date := soup.find("h6", {"class": "coh-heading"}):
            try:
                date = date.text.strip()
                year = datetime.strptime(date, "%B %d, %Y").year
            except (AttributeError, TypeError, ValueError):
                year = None
            return year
        return None

    @staticmethod
    def _parse_labels(soup: BeautifulSoup) -> list[int] | None:
        metadata = Scraper.__parse_metadata(soup)
        if labels := metadata.get("goals"):
            labels = re.findall(pattern=r"\d+", string="".join(labels))
            labels = sorted(map(int, labels))
        return labels

    @staticmethod
    def _parse_urls(soup: BeautifulSoup) -> set[str]:
        anchors = soup.find_all("a", {"class": "download-btn"})
        urls = {a.get("href") for a in anchors if a.get("href", "").endswith(".pdf")}
        return urls

    @staticmethod
    def __parse_metadata(soup: BeautifulSoup) -> dict:
        menu = soup.find("div", {"class": "publication-menu"})
        metadata = {}
        for div in menu.find_all("div", {"class": "coh-row-inner"}):
            k, v = None, None
            if h6 := div.find("h6"):
                k = h6.text.strip().lower().split()[-1]
            if nav := div.find("nav", {"class": "menu"}):
                v = [a.text.strip() for a in nav.find_all("a")]
            if k is not None and v is not None:
                metadata[k] = v
        return metadata
