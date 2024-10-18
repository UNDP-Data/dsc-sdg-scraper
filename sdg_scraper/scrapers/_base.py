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

from ..entities import File, Publication
from ..utils import download_file, write_content


class BaseScraper(ABC):
    """
    Base scraper class from which other scrapers inherit.

    Methods
    -------
    parse_listing(self, page: int)
        Parse a webpage listing publications to get URLs to publication pages.
    parse_publication(self, url: str)
        Parse a publication page and download PDF files.
    """

    def __init__(
        self,
        url_base: str,
        folder_path: str,
        max_connections: int = 4,
        download_mode: Literal["files", "text"] = "files",
        verbose: bool = False,
        **kwargs,
    ):
        """
        Initialise an instance of the base class.

        Parameters
        ----------
        url_base : str
            Base URL for the websites of interest.
        folder_path : str
            Directory to save PDFs to. The directory must exist beforehand.
        max_connections : int, default=4
            Maximum number of concurrent connections.
        download_mode : Literal["files", "text"], default="files"
            Mode for controlling which class method is used to download content.
        verbose :  bool, default=False
            When True, provide more output for monitoring.
        kwargs : dict
            Additional keyword arguments passed to `AsyncClient`.
        """
        self.url_base = url_base
        self.folder_path = folder_path
        self._urls = set()
        self.pubs = []
        self.download_mode = download_mode
        self.verbose = verbose
        self.limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=None,
            keepalive_expiry=5.0,
        )
        self.client = httpx.AsyncClient(
            **kwargs,
            follow_redirects=True,
            limits=self.limits,
        )

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
        click.echo("Scraping listing pages...")
        tasks = [self.parse_listing(page=page) for page in pages]
        await tqdm.gather(*tasks)
        click.echo(f"Scraping publications and saving files to {self.folder_path}...")
        tasks = [self.parse_publication(url=url) for url in self.urls]
        await tqdm.gather(*tasks)

    @abstractmethod
    async def parse_listing(self, page: int) -> None:
        """
        Source-specific method to parse a webpage listing publications to get
        URLs to publication pages. This method should be overridden in a subclass.

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
    async def parse_publication(self, url: str):
        """
        Parse a publication page and download PDF files.

        Parameters
        ----------
        url : str
            URL of a publication webpage.

        Raises
        ------
        HTTPError
            If the response code is not 200.
        """
        try:
            response = await self.client.get(url=url)
            response.raise_for_status()
        except httpx.HTTPError:
            click.echo(f"Failed to fetch {url}.", err=True)
            return
        soup = BeautifulSoup(response.content, features="lxml")
        labels = self._parse_labels(soup)
        if labels is None:
            if self.verbose:
                click.echo(f"Publication at {url} has no labels.")
            return
        match self.download_mode:
            case "files":
                urls = self._parse_urls(soup)
                files = await self._download_files(urls)
            case "text":
                text = self._parse_text(soup)
                content = text.encode("utf-8")
                file_name = await write_content(content, "txt", self.folder_path)
                files = [File(url=url, name=file_name)]
            case _:
                raise ValueError(f"Unhandled case: {self.download_mode}")
        pub = Publication(
            source=url,
            title=self._parse_title(soup),
            type=self._parse_type(soup),
            year=self._parse_year(soup),
            labels=self._parse_labels(soup),
            files=files or None,
        )
        self.pubs.append(pub)

    @staticmethod
    @abstractmethod
    def _parse_title(soup: BeautifulSoup) -> str | None:
        pass

    @staticmethod
    @abstractmethod
    def _parse_type(soup: BeautifulSoup) -> str | None:
        pass

    @staticmethod
    @abstractmethod
    def _parse_year(soup: BeautifulSoup) -> int | None:
        pass

    @staticmethod
    @abstractmethod
    def _parse_labels(soup: BeautifulSoup) -> list[int] | None:
        pass

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
    def urls(self) -> list[str]:
        """
        Get URLs collected from listings.

        Returns
        -------
        list[str]
            URLs for download files from.
        """
        return list(self._urls)

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
