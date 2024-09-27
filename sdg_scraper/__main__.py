"""
A command line interface for scraping.
"""

import importlib

import click

from .utils import list_scrapers


@click.group()
def cli():
    """A simple CLI for scraping."""
    pass


@cli.command()
def list():
    """List available sources/scrapers."""
    scrapers = list_scrapers()
    click.echo(scrapers)


if __name__ == "__main__":
    cli()
