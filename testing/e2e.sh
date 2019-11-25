#!/usr/bin/env bash

set -e

INIT_TEMPLATE_URL="https://service-catalog-tools.s3.eu-west-2.amazonaws.com/puppet/latest/servicecatalog-puppet-initialiser.template.yaml"
ENABLED_REGIONS="eu-west-1,eu-west-2"
ACCCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)


echo "installing the framework into your account"
aws cloudformation create-stack \
	--stack-name service-catalog-puppet-initialiser \
	--template-body ${INIT_TEMPLATE_URL} \
	--parameters \
	    ParameterKey=EnabledRegions,ParameterValue=\"${ENABLED_REGIONS}\" \
	    ParameterKey=ShouldCollectCloudformationEvents,ParameterValue=true \
	    ParameterKey=ShouldForwardEventsToEventbridge,ParameterValue=true \
	    ParameterKey=ShouldForwardFailuresToOpscenter,ParameterValue=true \
	--capabilities CAPABILITY_NAMED_IAM
aws cloudformation wait stack-create-complete --stack-name service-catalog-puppet-initialiser

echo "installing the tools locally"
virtualenv --python=Python3.7 venv
venv/bin/pip install aws-service-catalog-puppet

echo "setting up some products"
git clone --config 'credential.helper=!aws codecommit credential-helper $@' --config 'credential.UseHttpPath=true' https://git-codecommit.${AWS_DEFAULT_REGION}.amazonaws.com/v1/repos/ServiceCatalogPuppet
venv/bin/servicecatalog-puppet seed simple ServiceCatalogPuppet
venv/bin/servicecatalog-puppet import-product-set ServiceCatalogPuppet/manifest.yaml aws-iam example-simple-central-it-team-portfolio
#cd ServiceCatalogPuppet && sed 's|<YOUR_ACCOUNT_ID>|'"${ACCOUNT_ID}"'|' manifest.yaml  | tee manifest.yaml && git add . && git commit -am "initial add" && git push

