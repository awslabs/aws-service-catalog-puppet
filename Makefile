help:
	@echo "Usage:"
	@echo "    make help        show this message"
	@echo "    make setup       create virtual environment and install dependencies"
	@echo "    make activate    enter virtual environment"
	@echo "    make test        run the test suite"
	@echo "    exit             leave virtual environment"

setup:
	pip install pipenv
	pipenv install --dev --three
	
setup-aws:
	pip install pipenv
	pipenv lock -r > requirements.txt
	pip install -r requirements.txt
	pipenv lock -r -d > requirements-dev.txt
	pip install -r requirements-dev.txt
	
activate:
	pipenv shell -c

test:
	pipenv check
	pipenv run pytest --cov=./servicecatalog_puppet --cov-branch
	
test-aws:
	pipenv check
	pytest --cov=./servicecatalog_puppet --cov-branch	

prepare-deploy:
	pipenv run pipenv-setup sync
	pipenv run python setup.py sdist

prepare-deploy-aws:
	pip install pipenv-setup
	pipenv-setup sync
	python setup.py sdist

.PHONY: help activate test setup prepare-deploy test-aws setup-aws prepare-deploy-aws
