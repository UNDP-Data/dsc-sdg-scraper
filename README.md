# dsc-sdg-scraper

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![License](https://img.shields.io/github/license/undp-data/st-undp)](https://github.com/undp-data/st-undp/blob/main/LICENSE)
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://conventionalcommits.org)

A collection of web scrapers to harvest SDG-labelled publications. The project is written
in Python using an async interface of [`httpx`](https://www.python-httpx.org) and exposed
to users via a simple command line interface (CLI) built in [`click`](https://click.palletsprojects.com/en/8.1.x/).

## Table of Contents

- [Getting Started](#getting-started)
- [Usage](#usage)
- [License](#license)
- [Contributing](#contributing)

## Getting Started

These instructions will help you set up the project locally. The project has been developed and tested with Python `3.11`.
To set up a local environment:

1. Clone the repository:

```shell
git clone https://github.com/undp-data/dsc-sdg-scraper.git
```

2. Navigate to the project directory:

```shell
cd dsc-sdg-scraper
```

3. Create a virtual environment:

```shell
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

4. Install dependencies:

```shell
pip install -r requirements.txt
```

5. Explore the CLI:

```shell
python -m sdg_scraper
```

## Usage

The CLI enables you to run scrapers for any of the supported sources.

To list available sources, run:

```shell
python -m sdg_scraper list
```

To scrape a specific source, run:

```shell
python -m sdg_scraper run <source>
```

By default, the programme will scrape resources from the first two pages of the source (pages 0-1) and save the
files and metadata to the current directory. To customise this behaviour, use the command line options:

```shell
python -m sdg_scraper run <source> --pages 1 10 -f data
# or
python -m sdg_scraper run <source> -p 1 10 -f data
```

Use CLI help for more details:

```shell
python -m sdg_scraper --help
```

## License

This project's codebase is licensed under the BSD 3-Clause License. Data collected by the scraper may
be licensed under a different clause or even copyrighted. It is your responsibility to ensure that
any processing of data with the help of the scraper is responsible, ethical and legal.

## Contributing

All contributions must follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
The codebase is formatted with `black` and `isort`. Use the provided [Makefile](./Makefile) for these
routine operations.

1. Clone or fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes. Include tests for new features.
4. Run tests (`make test`).
5. Ensure your code is properly formatted (`make format`).
6. Commit your changes (`git commit -m 'Feat: add some feature'`).
7. Push to the branch (`git push origin feature-branch`).
8. Open a pull request.
