"""
A test suite for the CLI.
"""

import pytest
from click.testing import CliRunner

from sdg_scraper import __main__ as cli
from sdg_scraper.utils import list_scrapers


def test_list():
    runner = CliRunner()
    result = runner.invoke(cli.list)
    assert result.exit_code == 0
    assert "undp" in result.output


@pytest.mark.parametrize(
    "source",
    list_scrapers(),
)
def test_run(source, tmp_path):
    runner = CliRunner()
    path = tmp_path / source
    path.mkdir()
    result = runner.invoke(cli.run, [source, "-p", "1", "1", "-f", str(path)])
    assert result.exit_code == 0
    assert len(list(path.glob("publications-*.jsonl"))) == 1, "Metadata file is missing"
    assert len(list(path.glob("*.pdf"))) > 0, "No files have been downloaded"
