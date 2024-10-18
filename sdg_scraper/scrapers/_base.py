"""
A base scraper class from which other scrapers inherit.
"""

import asyncio
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Iterable, Literal, final

import click
import httpx
import pandas as pd
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm

from ..entities import Card, File, Metadata, Publication, Settings
from ..utils import download_file, write_content


class BaseScraper(ABC):
    """
    Base scraper class from which other scrapers inherit.

    Methods
    -------
    collect_cards(self, page: int)
        Collect publication cards from a listing page to get URLs to publication pages.
    process_card(self, card: Card)
        Parse a publication page and download publication text or files.
    """

    def __init__(
        self,
        url_base: str,
        settings: Settings | None = None,
        download_mode: Literal["files", "text"] = "files",
        **kwargs,
    ):
        """
        Initialise an instance of the base class.

        Parameters
        ----------
        url_base : str
            Base URL for the websites of interest.
        settings : Settings
            Scraper settings defining directories, concurrency, verbosity etc.
        download_mode : Literal["files", "text"], default="files"
            Mode for controlling which class method is used to download content.
        kwargs : dict
            Additional keyword arguments passed to `AsyncClient`.
        """
        self.url_base = url_base
        self.__settings = settings or Settings()
        self.__limits = httpx.Limits(
            max_connections=self.__settings.max_connections,
            max_keepalive_connections=None,
            keepalive_expiry=5.0,
        )
        self.client = httpx.AsyncClient(
            **kwargs,
            http2=self.__settings.http2,
            follow_redirects=True,
            limits=self.__limits,
        )
        self.download_mode = download_mode
        self.cards = set()
        self.pubs = []
        self.semaphore = asyncio.Semaphore(self.__settings.max_requests)

    async def __aenter__(self):
        await self.client.__aenter__()
        click.echo("Opened the client...")
        response = await self.client.get(self.url_base)
        click.echo(f"Network protocol: {response.http_version}")
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.client.aclose()
        click.echo("Closed the client.")

    @final
    async def __call__(self, pages: list[int]) -> None:
        click.echo("Collecting cards from listing pages...")
        await tqdm.gather(*[self.collect_cards(page=page) for page in pages])
        click.echo(f"Processing cards and saving publications to {self.folder_path}...")
        await tqdm.gather(*[self.process_card(card) for card in self.cards])

    @abstractmethod
    async def collect_cards(self, page: int) -> None:
        """
        Source-specific method to collect publication cards from a listing page. The cards
        hold URLs to individual publication pages and arbitrary metadata. This method must
        be overridden in a subclass.

        Parameters
        ----------
        page : int
            Page number the parse publications from.

        Returns
        -------
        None
        """
        pass

    @final
    async def process_card(self, card: Card) -> None:
        """
        Parse a publication page and download publication text or files.

        Parameters
        ----------
        card : Card
            Scraped Card object containing a URL and optional metadata.

        Raises
        ------
        HTTPError
            If the response code is not 200.
        """
        try:
            async with self.semaphore:
                response = await self.client.get(url=card.url)
                response.raise_for_status()
        except httpx.HTTPError:
            click.echo(f"Failed to fetch {card.url}.", err=True)
            return
        soup = BeautifulSoup(response.content, features="lxml")
        labels = self._parse_labels(soup)
        if labels is None:
            if self.__settings.verbose:
                click.echo(f"Publication at {card.url} has no labels.")
            return
        match self.download_mode:
            case "files":
                urls = self._parse_urls(soup)
                files = await self._download_files(urls)
            case "text":
                text = self._parse_text(soup)
                content = text.encode("utf-8")
                file_name = await write_content(content, "txt", self.folder_path)
                files = [File(url=card.url, name=file_name)]
            case _:
                raise ValueError(f"Unhandled case: {self.download_mode}")
        metadata = self._parse_metadata(soup, card)
        pub = Publication(**metadata.model_dump(), files=files or None)
        self.pubs.append(pub)

    def _parse_metadata(self, soup: BeautifulSoup, card: Card) -> Metadata:
        if card.metadata is None:
            metadata = Metadata(
                source=card.url,
                title=self._parse_title(soup),
                type=self._parse_type(soup),
                year=self._parse_year(soup),
                labels=self._parse_labels(soup),
            )
        else:
            raise NotImplementedError
        return metadata

    @staticmethod
    def _parse_title(soup: BeautifulSoup) -> str | None:
        raise NotImplementedError

    @staticmethod
    def _parse_type(soup: BeautifulSoup) -> str | None:
        raise NotImplementedError

    @staticmethod
    def _parse_year(soup: BeautifulSoup) -> int | None:
        raise NotImplementedError

    @staticmethod
    def _parse_labels(soup: BeautifulSoup) -> list[int] | None:
        raise NotImplementedError

    @staticmethod
    def _parse_urls(soup: BeautifulSoup) -> set[str]:
        """
        Parse URLs to publications from a webpage content. This method needs to be overridden
        only by scrapers that collect files, not text.

        Parameters
        ----------
        soup : BeautifulSoup
            Contents of a webpage as a bs4 object.

        Returns
        -------
        set[str]
            Unique URLs to publications.
        """
        raise NotImplementedError

    @staticmethod
    def _parse_text(soup: BeautifulSoup) -> str:
        """
        Parse text from a webpage content. This method needs to be overridden
        only by scrapers that collect text, not files.

        Parameters
        ----------
        soup : BeautifulSoup
            Contents of a webpage as a bs4 object.

        Returns
        -------
        str
            Parsed SDG-related text.
        """
        raise NotImplementedError

    @final
    async def _download_files(self, urls: Iterable[str]) -> list[File]:
        """
        Download files from a list of URLs.

        Parameters
        ----------
        urls : Iterable[str]
            URLs to download files from.

        Returns
        -------
        files : list[File]
            List of file objects.
        """
        tasks = [download_file(self.client, url, self.folder_path) for url in urls]
        files = await asyncio.gather(*tasks)
        return files

    @property
    @final
    def settings(self) -> Settings:
        """
        Get scraper settings.

        Returns
        -------
        Settings
            Scraper settings object.
        """
        return self.__settings

    @property
    @final
    def folder_path(self) -> str:
        """
        Get a path to the folder for saving publications.

        Returns
        -------
        str
            Path to the folder.
        """
        return self.__settings.folder_path

    @property
    @final
    def urls(self) -> list[str]:
        """
        Get URLs collected from listings.

        Returns
        -------
        list[str]
            URLs for download files from.
        """
        return [card.url for card in self.cards]

    @property
    @final
    def df_pubs(self) -> pd.DataFrame:
        """
        Get publication metadata in Pandas DataFrame.

        Returns
        -------
        df_pubs : pd.DataFrame
            Publication metadata from `self.pubs` attribute as a Pandas DataFrame.
        """
        df_pubs = pd.DataFrame([pub.model_dump() for pub in self.pubs])
        return df_pubs

    @final
    def export(self) -> str:
        """
        Export publication metadata to disk in a JSON lines format.

        Returns
        -------
        file_path : str
            Path to the saved file.
        """
        file_name = f"publications-{datetime.now(timezone.utc):%y%m%d-%H%M%S}.jsonl"
        file_path = os.path.join(self.folder_path, file_name)
        self.df_pubs.to_json(file_path, orient="records", lines=True)
        return file_path
