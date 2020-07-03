.PHONY: help install pre-build build bump-patch bump-minor bump-major

help:
	@echo "Usage:"
	@echo "    make help        show this message"
	@echo "    make install     install dependencies"
	@echo "    make pre-build   run tests"
	@echo "    make build       build the package"
	@echo "    exit             leave virtual environment"

install:
	pip install poetry
	poetry install

pre-build:
	poetry run pytest -vv -k unit --cov=./servicecatalog_puppet --cov-branch

build:
	poetry build

bump-patch:
	dephell project bump patch

bump-minor:
	dephell project bump minor

bump-major:
	dephell project bump major
