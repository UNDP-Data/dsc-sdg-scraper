"""
A scraper for IOM Blogs, News and Stories (https://www.iom.int/search).
"""

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..entities import Card, Metadata, Settings
from ._base import BaseScraper


class Scraper(BaseScraper):
    """
    Scraper for IOM Blogs, News and Stories (https://www.iom.int/search).
    """

    def __init__(self, settings: Settings | None = None):
        super().__init__(
            url_base="https://www.iom.int",
            settings=settings,
            download_mode="text",
        )

    async def collect_cards(self, page: int = 0) -> None:
        url = f"{self.url_base}/search"
        params = {
            "keywords": "",
            "type[0]": "blog_list",
            "type[1]": "featured_stories",
            "type[2]": "press_release",
            "region_country": "",
            "sdgs[0]": "1960",  # SDG 1
            "sdgs[1]": "1961",
            "sdgs[2]": "1962",
            "sdgs[3]": "1964",
            "sdgs[4]": "1963",
            "sdgs[5]": "1973",
            "sdgs[6]": "1967",
            "sdgs[7]": "1965",
            "sdgs[8]": "1966",  # SDG 9
            "sdgs[9]": "1968",
            "sdgs[10]": "1969",
            "sdgs[11]": "1976",
            "sdgs[12]": "1970",
            "sdgs[13]": "1975",
            "sdgs[14]": "1974",
            "sdgs[15]": "1971",
            "sdgs[16]": "1972",  # SDG 17
            "created": "All",
            "sort_bef_combine": "created_DESC",
            "page": page,
        }
        if (soup := await self.get_soup(url, params)) is None:
            return
        cards = soup.find_all("div", {"class": "article-detail"})
        # take the parent tag since stories are not nested within cards properly
        for card in cards:
            card = card.parent
            url = card.find("a").get("href")
            # handle urls differently as stories use a subdomain
            if not url.startswith("http"):
                url = urljoin(self.url_base, url)
            metadata = {
                "title": self._parse_title(card),
                "type": self._parse_type(card),
                "year": self._parse_year(card),
            }
            card = Card(url=url, metadata=metadata)
            self.cards.add(card)

    def _parse_metadata(self, soup: BeautifulSoup, card: Card) -> Metadata:
        metadata = Metadata(
            source=card.url,
            **card.metadata,
            labels=self._parse_labels(soup),
        )
        return metadata

    @staticmethod
    def _parse_title(soup: BeautifulSoup) -> str | None:
        if h5 := soup.find("h5", {"class": "title"}):
            title = h5.text.strip()
            return title
        return None

    @staticmethod
    def _parse_type(soup: BeautifulSoup) -> str | None:
        if tag := soup.find("div", {"class": "tag"}):
            kind = re.sub(r"\s+", " ", tag.text.strip())
            return kind
        return None

    @staticmethod
    def _parse_year(soup: BeautifulSoup) -> int | None:
        date = soup.find("div", {"class": "date"})
        try:
            date = re.search(r"(\d{4})", date.text).group()
            year = int(date)
        except (AttributeError, TypeError, ValueError):
            year = None
        return year

    @staticmethod
    def _parse_labels(soup: BeautifulSoup) -> list[int] | None:
        attrs = {"class": "field--name-dynamic-block-fieldnode-sdg-sorted"}
        pattern = r"/public/sdg.*/e_web_(\d{2}).*\.png"
        regex = re.compile(pattern)
        if div := soup.find("div", attrs):
            soup = div
        labels = []
        for img in soup.find_all("img", src=regex):
            # "[...]/sdgs-icon/e_web_10.png?itok=68_FmtiD" -> 10
            if match := re.search(pattern, img.get("src")):
                label = int(match.group(1))
                labels.append(label)
        if not labels:
            return None
        labels.sort()
        return labels

    @staticmethod
    def _parse_text(soup: BeautifulSoup) -> str | None:
        # blog
        if div := soup.find("div", {"class": "node--type-blog-list"}):
            div = div.find("div", {"class": "field--name-field-contents"})
        # news
        elif div := soup.find("div", {"class": "narrow-content"}):
            div = div.find("div", {"class": "field--type-text-with-summary"})
        # stories
        elif div := soup.find("div", {"data-history-node-id": re.compile(r"\d+")}):
            pass
        if div is None:
            return None
        return div.text.strip()
