.PHONY: install install-dev test lint format package deploy clean

PYTHON := python
PIP := $(PYTHON) -m pip
PYTEST := pytest
ENV ?= dev

install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements-dev.txt

test:
	$(PYTEST) tests/

lint:
	flake8 src tests
	pylint src --disable=C0111,C0103
	mypy src

format:
	black src tests

clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov dist lambda-deployment.zip
	find . -type d -name "__pycache__" -exec rm -rf {} +

package: clean
	mkdir -p dist
	cp -r src dist/
	$(PIP) install -r requirements.txt --target dist/
	cd dist && zip -r ../lambda-deployment.zip .

deploy:
	bash scripts/deploy.sh $(ENV)
