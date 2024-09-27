"""
Utility functions for scraping files.
"""

import os
from hashlib import md5

import httpx

__all__ = ["get_file_id", "download_file"]


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


async def download_file(
    client: httpx.AsyncClient,
    url: str,
    folder_path: str = None,
    file_extension: str = "pdf",
    headers: dict = None,
) -> str:
    """
    Download a PDF file from a URL and save it to folder_path.

    Note that since the file name is based on an MD5 checksum of its contents, there is no way to know if the file
    already exists to avoid repeated downloads. In practice, using a URL to identify a PDF is not an option either for
    the same publication file can appear on different websites (and under different names too).

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
    file_path : str
        Path to the downloaded file.

    Raises
    ------
    httpx.HTTPStatusError
        If the response code is not 200.
    """
    response = await client.get(url=url, headers=headers)
    response.raise_for_status()

    # construct a file name and path
    file_id = get_file_id(response.content)
    file_name = f"{file_id}.{file_extension}"
    file_path = os.path.join(folder_path or "", file_name)

    with open(file_path, "wb") as file:
        file.write(response.content)
    return file_path
