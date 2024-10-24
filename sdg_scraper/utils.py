"""
Utility functions for scraping files.
"""

import asyncio
import importlib
import os
import pkgutil
from functools import wraps
from hashlib import md5
from typing import Callable

import aiofiles
import click
import httpx

from .entities import File

__all__ = [
    "get_file_id",
    "write_content",
    "download_file",
    "list_scrapers",
    "make_sync",
]


def get_file_id(content: bytes) -> str:
    """
    Get an MD5 checksum of file contents to be used as a unique file ID.

    Parameters
    ----------
    content : bytes
        Contents of a file as bytes.

    Returns
    -------
    file_id : str
        MD5 checksum of the contents.
    """
    file_id = md5(content).hexdigest()
    return file_id


async def write_content(content: bytes, extension: str, folder_path: str = None) -> str:
    """
    Asynchronously write content to a file.

    Parameters
    ----------
    content : bytes
        Contents of a file as bytes.
    extension : str
        Extension of the file to be saved.
    folder_path : str, optional
        Path to the folder where the file will be saved.

    Returns
    -------
    file_name : str
        Unique file name based on the hash of file contents.
    """
    # construct a file name and path
    file_id = get_file_id(content)
    file_name = f"{file_id}.{extension}"
    file_path = os.path.join(folder_path or "", file_name)
    async with aiofiles.open(file_path, mode="wb") as file:
        await file.write(content)
    return file_name


async def download_file(
    client: httpx.AsyncClient,
    url: str,
    folder_path: str = None,
    file_extension: str = "pdf",
    headers: dict = None,
) -> File:
    """
    Download a PDF file from a URL and save it to folder_path.

    Note that since the file name is based on an MD5 checksum of its contents, there is no way
    to know if the file already exists to avoid repeated downloads. In practice, using a URL
    to identify a PDF is not an option either for the same publication file can appear on
    different websites (and under different names too).

    Parameters
    ----------
    client : httpx.AsyncClient, optional
        Existing client instance if applicable.
    url : str
        URL of the file to be downloaded.
    folder_path : str, optional
        Path to the folder where the file will be saved. Defaults to the current directory.
    file_extension : str, default="pdf"
        Extension to use for the downloaded file.
    headers : dict, optional
        Custom headers passed to the GET call.

    Returns
    -------
    file : File
        Entity containing the URL and downloaded file name. If a download failed, the name is None.

    Raises
    ------
    httpx.HTTPStatusError
        If the response code is not 200.
    """
    try:
        response = await client.get(url=url, headers=headers)
        response.raise_for_status()
    except httpx.HTTPError:
        click.echo(f"Could not download a file from {url}.", err=True)
        return File(url=url, name=None)
    file_name = await write_content(response.content, file_extension, folder_path)
    file = File(url=url, name=file_name)
    return file


def list_scrapers() -> list[str]:
    """
    List public package modules under scrapers subpackage.

    Returns
    -------
    scrapers : list[str]
        Scraper modules available.
    """
    package = importlib.import_module(f"{__package__}.scrapers")
    modules = pkgutil.iter_modules(package.__path__)
    scrapers = [name for _, name, _ in modules if not name.startswith("_")]
    return scrapers


def make_sync(func: Callable) -> Callable:
    """
    A decorator to make an async function run in a synchronous context.

    This is only used for the CLI. See https://github.com/pallets/click/issues/2033.

    Parameters
    ----------
    func : Callable
        A function to be decorated.

    Returns
    -------
    wrapped : Callable
        Function wrapper that calls asyncio internally.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper
