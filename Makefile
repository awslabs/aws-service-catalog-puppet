.PHONY: help install pre-build build bump-patch bump-minor bump-major version bootstrap bootstrap-branch expand deploy clean deploy-spoke black pycodestyle

WS=ignored/testing/$(ENV_NUMBER)
FACTORY_VENV=${WS}/factory
PUPPET_VENV=${WS}/puppet

include Makefile.Test

help: ## Prints help message
	@IFS=$$'\n' ; \
	help_lines=(`fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##/:/'`); \
	printf "%-30s %s\n" "Target" "Description" ; \
	printf "%-30s %s\n" "------" "-----------------------------------------------------------------------------------";\
	for help_line in $${help_lines[@]}; do \
		IFS=$$':' ; \
		help_split=($$help_line) ; \
		help_command=`echo $${help_split[0]} | sed -e 's/^ *//' -e 's/ *$$//'` ; \
		help_info=`echo $${help_split[2]} | sed -e 's/^ *//' -e 's/ *$$//'` ; \
		printf '\033[36m'; \
		printf "%-30s %s" $$help_command ; \
		printf '\033[0m'; \
		printf "%s\n" $$help_info; \
	done

install: ## Installs the checked out version of the code to your poetry managed venv
	poetry install

pre-build: black unit-tests ## CI action to run before the build.  Runs black and unit tests.

build: ## Builds the project into an sdist
	poetry build -f sdist

bump-patch:
	poetry version patch

bump-minor:
	poetry version minor

bump-major:
	poetry version major

version: ## runs servicecatalog-puppet version
	poetry run servicecatalog-puppet version

bootstrap: ## runs servicecatalog-puppet --info bootstrap
	poetry run servicecatalog-puppet --info bootstrap

bootstrap-self-as-spoke: ## servicecatalog-puppet --info bootstrap-spoke for the current aws profile
	poetry run servicecatalog-puppet --info bootstrap-spoke $$(aws sts get-caller-identity --query Account --output text)

bootstrap-branch: ## runs run servicecatalog-puppet --info bootstrap-branch for the local checkout branch
	poetry run servicecatalog-puppet --info bootstrap-branch \
		$$(git rev-parse --abbrev-ref HEAD)

expand: ## runs servicecatalog-puppet --info expand for the checked out manifest file
	poetry run servicecatalog-puppet --info expand \
		ignored/src/ServiceCatalogPuppet/manifest.yaml

deploy: ## runs servicecatalog-puppet --info deploy
	poetry run servicecatalog-puppet --info deploy \
		ignored/src/ServiceCatalogPuppet/manifest-expanded.yaml

clean: ## cleans up after a build
	rm -rf data results output config.yaml

deploy-spoke: ## runs servicecatalog-puppet --info deploy for a spoke
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

black: ## runs black on the checked out code
	poetry run black servicecatalog_puppet

pycodestyle: ## runs pycodestyle on the the checked out code
	poetry run pycodestyle --statistics -qq servicecatalog_puppet

prepare-for-testing: build ## generates a setup.py so you can test bootstrapped branches in AWS Codecommit
	tar -zxvf dist/aws-service-catalog-puppet-*.tar.gz -C dist aws-service-catalog-puppet-*/setup.py
	mv aws-service-catalog-puppet-*/setup.py setup.py
