"""
A command line interface for scraping.
"""

import importlib

import click

from .utils import list_scrapers, make_sync


@click.group()
def cli():
    """A simple CLI for scraping."""
    pass


@cli.command()
def list():
    """List available sources/scrapers."""
    scrapers = list_scrapers()
    click.echo(scrapers)


@cli.command()
@click.option(
    "--source",
    "-s",
    type=click.Choice(list_scrapers(), case_sensitive=False),
    help="The name of the source to scrape.",
)
@click.option(
    "--folder",
    "-f",
    type=str,
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
@make_sync
async def run(source, folder, pages):
    """Run a scraper for a given source."""
    # dynamically import the module and scraper
    module = importlib.import_module(f".scrapers.{source}", __package__)
    scraper = module.Scraper(folder_path=folder)
    async with scraper:
        await scraper(pages=range(pages[0], pages[1] + 1))
    scraper.export()
    click.echo("Completed.")


if __name__ == "__main__":
    cli()
