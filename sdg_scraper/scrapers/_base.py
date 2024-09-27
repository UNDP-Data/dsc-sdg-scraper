"""
A base scraper class from which other scrapers inherit.
"""

import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import final

import click
import httpx
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

from ..entities import Publication
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
            Headers to be passed to GET call in `requests` while scraping.
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
        for page in tqdm(pages):
            await self.parse_listing(page=page)
        click.echo("Scraping publication pages...")
        for url in tqdm(self.urls):
            await self.parse_publication(url=url)
        click.echo("Done.")

    @abstractmethod
    async def parse_listing(self, page: int) -> None:
        """
        Source-specific method to parse a webpage listing publications to get
        URLs to publication pages. This method should be overridden in a subclass.

        Parameters
        ----------
        page : int
            Page number for pagination.

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
        response = await self.client.get(url=url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, features="lxml")
        labels = self._parse_labels(soup)
        if labels is None:
            click.echo(f"Publication at {url} has no labels.")
            return
        urls = self._parse_urls(soup)
        pdfs = await self._download_files(urls)
        files = [{"url": url, "pdf": pdf} for url, pdf in zip(urls, pdfs)]
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
    async def _download_files(self, urls: list[str]) -> list[str | None]:
        """
        Download PDFs from a list of URLs.

        Parameters
        ----------
        urls : list[str]
            List of URLs to download PDFs from.

        Returns
        -------
        pdfs : list[str]
            List of paths to PDF files. For failed downloads, the path is an empty string.
        """
        pdfs = []
        for url in urls:
            try:
                pdf = await download_file(
                    client=self.client,
                    url=url,
                    folder_path=self.folder_path,
                )
                pdfs.append(pdf)
            except httpx.HTTPStatusError:
                click.echo(f"Could not download a PDF from {url}.")
                pdfs.append(None)
        return pdfs

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
