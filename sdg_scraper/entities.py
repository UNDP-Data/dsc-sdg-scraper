"""
Entity (data) models with in-built type validation.
"""

from pydantic import BaseModel, Field

__all__ = ["Card", "File", "Metadata", "Publication", "Settings"]


class Card(BaseModel):
    """
    Publication card from a listing page.

    When compared, card URLs are used while metadata are ignored.
    """

    def __hash__(self):
        return hash(self.url)

    def __eq__(self, other):
        if isinstance(other, Card):
            return self.url == other.url
        return False

    url: str = Field(
        description="URL to a full publication.",
        examples=["https://www.undp.org/publications/climate-dictionary"],
    )
    metadata: dict | None = Field(
        default=None,
        description="Arbitrary metadata related to the publication.",
    )


class File(BaseModel):
    """File object from a publication page."""

    url: str = Field(
        description="A URL to a file.",
        examples=[
            "https://www.undp.org/sites/g/files/zskgke326/files/2023-10/undp-the-climate-dictionary-v3.pdf"
        ],
    )
    name: str | None = Field(
        default=None,
        description="Name of the downloaded file, corresponding to the hash of its content.",
        examples=["bc2b6376fc5d16f9ea18824c32fba551.pdf"],
    )


class Metadata(BaseModel):
    """Publication metadata."""

    source: str = Field(
        description="Source URL to a publication page. Can be a direct URL or DOI redirect.",
        examples=["https://www.undp.org/publications/climate-dictionary"],
    )
    title: str | None = Field(
        description="Publication title.",
        examples=["The Climate Dictionary"],
    )
    type: str | None = Field(
        default=None,
        description="Publication type.",
        examples=["Guidelines, handbooks, toolkits"],
    )
    year: int | None = Field(
        description="Publication year.",
        examples=[2023],
    )
    labels: list[int] = Field(
        description="SDG labels for the publication.",
        examples=[[13, 17]],
    )


class Publication(Metadata):
    """Publication metadata and files."""

    files: list[File] | None = Field(
        default=None,
        description="""Files from the publication page. One publication can have
        multiple linked files.""",
    )


class Settings(BaseModel):
    """Scraper settings conrtolling concurrency, HTTP protocol, output location etc."""

    folder_path: str = Field(
        default="",
        description="Directory to save publications to. The directory must exist beforehand.",
    )
    max_connections: int = Field(
        default=4,
        description="Maximum number of concurrent connections.",
    )
    http2: bool = Field(
        default=True,
        description="When True, HTTP/2 protocol will be attempted for connections.",
    )
    verbose: bool = Field(
        default=False,
        description="When True, provide more output for monitoring.",
    )
