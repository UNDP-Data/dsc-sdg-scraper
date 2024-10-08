"""
A base scraper class from which other scrapers inherit.
"""

import asyncio
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import final

import click
import httpx
import pandas as pd
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm

from ..entities import File, Publication
from ..utils import download_file


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

    def __init__(self, url_base: str, folder_path: str, headers: dict = None):
        """
        Initialise an instance of the base class.

        Parameters
        ----------
        url_base : str
            Base URL for the websites of interest.
        folder_path : str
            Directory to save PDFs to. The directory must exist beforehand.
        headers : dict, optional
            Headers to be passed to GET call.
        """
        self.url_base = url_base
        self.folder_path = folder_path
        self.headers = headers
        self._urls = set()
        self.pubs = []

    async def __aenter__(self):
        self.client = httpx.AsyncClient(headers=self.headers, follow_redirects=True)
        click.echo("Opened the client...")
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
            click.echo(f"Publication at {url} has no labels.")
            return
        urls = self._parse_urls(soup)
        files = await self._download_files(urls)
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
    @abstractmethod
    def _parse_urls(soup: BeautifulSoup) -> list[str]:
        pass

    @final
    async def _download_files(self, urls: list[str]) -> list[File]:
        """
        Download files from a list of URLs.

        Parameters
        ----------
        urls : list[str]
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
