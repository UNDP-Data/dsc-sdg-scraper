"""
A command line interface for scraping.
"""

import importlib
import os

import click

from .utils import list_scrapers, make_sync


@click.group()
def cli():
    """A simple CLI for scraping."""
    pass


@cli.command()
def list():
    """List available sources/scrapers."""
    scrapers = "\n".join(list_scrapers())
    click.echo(scrapers)


@cli.command()
@click.argument(
    "source",
    type=click.Choice(list_scrapers(), case_sensitive=False),
)
@click.option(
    "--folder",
    "-f",
    type=str,
    default=os.getcwd(),
    help="Path to a folder to save files to.",
)
@click.option(
    "--pages",
    "-p",
    nargs=2,
    type=(int, int),
    default=(0, 1),
    show_default=True,
    help="A range of listing pages to scrape from.",
)
@click.option(
    "--connections",
    "-c",
    type=int,
    default=4,
    show_default=True,
    help="Maximum number of concurrent connections.",
)
@click.option(
    "--http2/--no-http2",
    default=True,
    help="Enable or disable support for HTTP/2 protocol (enabled by default).",
)
@make_sync
async def run(source, folder, pages, connections, http2):
    """Run a scraper for a given source.

    SOURCE The name of the source to scrape.
    """
    # dynamically import the module and scraper
    module = importlib.import_module(f".scrapers.{source}", __package__)
    scraper = module.Scraper(
        folder_path=folder,
        max_connections=connections,
        http2=http2,
    )
    async with scraper:
        await scraper(pages=range(pages[0], pages[1] + 1))
    scraper.export()
    click.echo("Completed.")


if __name__ == "__main__":
    cli()
