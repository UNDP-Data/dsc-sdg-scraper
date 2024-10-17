"""
Entity (data) models with in-built type validation.
"""

from pydantic import BaseModel, Field

__all__ = ["File", "Metadata", "Publication"]


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
