install:
	pip install --upgrade pip && pip install -r requirements_dev.txt
lint:
	pylint main.py sdg_scraper/
format:
	isort . --profile black --multi-line 3 && black .
test:
	python -m pytest tests/
