.PHONY: help install pre-build build bump-patch bump-minor bump-major version bootstrap bootstrap-branch expand deploy clean deploy-spoke black pycodestyle
.DEFAULT_GOAL := help

WS=ignored/testing/$(ENV_NUMBER)
FACTORY_VENV=${WS}/factory
PUPPET_VENV=${WS}/puppet

include Makefile.Test

## @CI_actions Installs the checked out version of the code to your poetry managed venv
install:
	poetry install

## @CI_actions Runs code quality checks
pre-build: black unit-tests

## @CI_actions Builds the project into an sdist
build:
	poetry build -f sdist

## @Project_setup Increment patch number
bump-patch:
	poetry version patch

## @Project_setup Increment minor number
bump-minor:
	poetry version minor

## @Project_setup Increment major number
bump-major:
	poetry version major

## @Puppet_commands Runs servicecatalog-puppet version
version:
	poetry run servicecatalog-puppet version

## @Puppet_commands Runs servicecatalog-puppet bootstrap
bootstrap:
	poetry run servicecatalog-puppet --info bootstrap

## @Puppet_commands Runs servicecatalog-puppet bootstrap-spoke for the current aws profile
bootstrap-self-as-spoke:
	poetry run servicecatalog-puppet --info bootstrap-spoke $$(aws sts get-caller-identity --query Account --output text)

## @Puppet_commands Runs servicecatalog-puppet --info bootstrap-branch for the local checkout branch
bootstrap-branch:
	poetry run servicecatalog-puppet --info bootstrap-branch \
		$$(git rev-parse --abbrev-ref HEAD)

## @Puppet_commands Runs servicecatalog-puppet --info expand for the checked out manifest file
expand:
	poetry run servicecatalog-puppet --info expand \
		ignored/src/ServiceCatalogPuppet/manifest.yaml

## @Puppet_commands Runs servicecatalog-puppet --info deploy
deploy:
	poetry run servicecatalog-puppet --info deploy \
		ignored/src/ServiceCatalogPuppet/manifest-expanded.yaml

## @Project_setup Cleans up after a build
clean:
	rm -rf data results output config.yaml

## @Puppet_commands Runs servicecatalog-puppet --info deploy for a spoke
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

## @Code_quality Runs black on the checked out code
black:
	poetry run black servicecatalog_puppet

## @Code_quality Runs pycodestyle on the the checked out code
pycodestyle:
	poetry run pycodestyle --statistics -qq servicecatalog_puppet

## @Project_setup Generates a setup.py so you can test bootstrapped branches in AWS Codecommit
prepare-for-testing: build
	tar -zxvf dist/aws-service-catalog-puppet-*.tar.gz -C dist aws-service-catalog-puppet-*/setup.py
	mv aws-service-catalog-puppet-*/setup.py setup.py



help: help-prefix help-targets

help-prefix:
	@echo Usage:
	@echo '  make <target>'
	@echo '  make <VAR>=<value> <target>'
	@echo ''
	@echo Targets:

HELP_TARGET_MAX_CHAR_NUM = 25

help-targets:
	@awk '/^[a-zA-Z\-\_0-9]+:/ \
		{ \
			helpMessage = match(lastLine, /^## (.*)/); \
			if (helpMessage) { \
				helpCommand = substr($$1, 0, index($$1, ":")-1); \
				helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
				helpGroup = match(helpMessage, /^@([^ ]*)/); \
				if (helpGroup) { \
					helpGroup = substr(helpMessage, RSTART + 1, index(helpMessage, " ")-2); \
					helpMessage = substr(helpMessage, index(helpMessage, " ")+1); \
				} \
				printf " %s|  %-$(HELP_TARGET_MAX_CHAR_NUM)s %s\n", \
					helpGroup, helpCommand, helpMessage; \
			} \
		} \
		{ lastLine = $$0 }' \
		$(MAKEFILE_LIST) \
	| sort -t'|' -sk1,1 \
	| awk -F '|' ' \
			{ \
			cat = $$1; \
			if (cat != lastCat || lastCat == "") { \
				if ( cat == "0" ) { \
					print "Targets:" \
				} else { \
					gsub("_", " ", cat); \
					printf "%s ~ \n", cat; \
				} \
			} \
			print " " $$2 \
		} \
		{ lastCat = $$1 }'
