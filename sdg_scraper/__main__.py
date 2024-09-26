"""
A command line interface for scraping.
"""

import click


@click.group()
def cli():
    """A simple CLI for scraping."""
    pass


if __name__ == "__main__":
    cli()
