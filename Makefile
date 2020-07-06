.PHONY: help install pre-build build bump-patch bump-minor bump-major version bootstrap bootstrap-branch expand deploy clean deploy-spoke black pycodestyle

help:
	@echo "Usage:"
	@echo "    make help        show this message"
	@echo "    make install     install dependencies"
	@echo "    make pre-build   run tests"
	@echo "    make build       build the package"
	@echo "    exit             leave virtual environment"

install:
	poetry install

pre-build:
	poetry run pytest -vv --exitfirst -k unit --junit-xml=reports/junit/junit.xml --cov=./servicecatalog_puppet --cov-branch

build:
	poetry build -f sdist

bump-patch:
	poetry version patch

bump-minor:
	poetry version minor

bump-major:
	poetry version major

version:
	poetry run servicecatalog-puppet version

bootstrap:
	poetry run servicecatalog-puppet --info bootstrap

bootstrap-spoke:
	poetry run servicecatalog-puppet --info bootstrap-spoke $$(aws sts get-caller-identity --query Account --output text)

bootstrap-branch:
	poetry run servicecatalog-puppet --info bootstrap-branch \
		$$(git rev-parse --abbrev-ref HEAD)

expand:
	poetry run servicecatalog-puppet --info expand \
		ignored/src/ServiceCatalogPuppet/manifest.yaml

deploy:
	poetry run servicecatalog-puppet --info deploy \
		ignored/src/ServiceCatalogPuppet/manifest-expanded.yaml

clean:
	rm -rf data results output

deploy-spoke:
	poetry run servicecatalog-puppet --info deploy \
		--execution-mode spoke \
		--puppet-account-id 863888216255 \
		--single-account 162541427941 \
		--home-region eu-west-1 \
		--regions eu-west-1,eu-west-2,eu-west-3 \
		--should-collect-cloudformation-events true \
		--should-forward-events-to-eventbridge true \
		--should-forward-failures-to-opscenter true \
		ignored/src/ServiceCatalogPuppet/manifest-expanded.yaml

black:
	poetry run black servicecatalog_puppet

pycodestyle:
	poetry run pycodestyle --statistics -qq servicecatalog_puppet

prepare-for-testing:
	poetry build -f sdist
	tar -zxvf dist/aws-service-catalog-puppet-*.tar.gz -C dist aws-service-catalog-puppet-*/setup.py
	mv aws-service-catalog-puppet-*/setup.py setup.py
