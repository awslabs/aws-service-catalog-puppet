import json
import os

import click
from betterboto import client as betterboto_client
from colorclass import Color
from terminaltables import AsciiTable

from servicecatalog_puppet.constants import LAUNCHES
from servicecatalog_puppet.core import get_regions
from servicecatalog_puppet.utils.manifest import build_deployment_map

import logging

logger = logging.getLogger(__file__)


def do_list_launches(manifest):
    click.echo("Getting details from your account...")
    ALL_REGIONS = get_regions(os.environ.get("AWS_DEFAULT_REGION"))
    deployment_map = build_deployment_map(manifest)
    account_ids = [a.get('account_id') for a in manifest.get('accounts')]
    deployments = {}
    for account_id in account_ids:
        for region_name in ALL_REGIONS:
            role = "arn:aws:iam::{}:role/{}".format(account_id, 'servicecatalog-puppet/PuppetRole')
            logger.info("Looking at region: {} in account: {}".format(region_name, account_id))
            with betterboto_client.CrossAccountClientContextManager(
                    'servicecatalog', role, 'sc-{}-{}'.format(account_id, region_name), region_name=region_name
            ) as spoke_service_catalog:

                response = spoke_service_catalog.list_accepted_portfolio_shares()
                portfolios = response.get('PortfolioDetails', [])

                response = spoke_service_catalog.list_portfolios()
                portfolios += response.get('PortfolioDetails', [])

                for portfolio in portfolios:
                    portfolio_id = portfolio.get('Id')
                    response = spoke_service_catalog.search_products_as_admin(PortfolioId=portfolio_id)
                    for product_view_detail in response.get('ProductViewDetails', []):
                        product_view_summary = product_view_detail.get('ProductViewSummary')
                        product_id = product_view_summary.get('ProductId')
                        response = spoke_service_catalog.search_provisioned_products(
                            Filters={'SearchQuery': ["productId:{}".format(product_id)]})
                        for provisioned_product in response.get('ProvisionedProducts', []):
                            launch_name = provisioned_product.get('Name')
                            status = provisioned_product.get('Status')

                            provisioning_artifact_response = spoke_service_catalog.describe_provisioning_artifact(
                                ProvisioningArtifactId=provisioned_product.get('ProvisioningArtifactId'),
                                ProductId=provisioned_product.get('ProductId'),
                            ).get('ProvisioningArtifactDetail')

                            if deployments.get(account_id) is None:
                                deployments[account_id] = {'account_id': account_id, 'launches': {}}

                            if deployments[account_id]['launches'].get(launch_name) is None:
                                deployments[account_id]['launches'][launch_name] = {}

                            deployments[account_id]['launches'][launch_name][region_name] = {
                                'launch_name': launch_name,
                                'portfolio': portfolio.get('DisplayName'),
                                'product': manifest.get('launches', {}).get(launch_name, {}).get('product'),
                                'version': provisioning_artifact_response.get('Name'),
                                'active': provisioning_artifact_response.get('Active'),
                                'region': region_name,
                                'status': status,
                            }
                            output_path = os.path.sep.join([
                                LAUNCHES,
                                account_id,
                                region_name,
                            ])
                            if not os.path.exists(output_path):
                                os.makedirs(output_path)

                            output = os.path.sep.join([output_path, "{}.json".format(provisioned_product.get('Id'))])
                            with open(output, 'w') as f:
                                f.write(json.dumps(
                                    provisioned_product,
                                    indent=4, default=str
                                ))

    table = [
        ['account_id', 'region', 'launch', 'portfolio', 'product', 'expected_version', 'actual_version', 'active',
         'status']
    ]
    for account_id, details in deployment_map.items():
        for launch_name, launch in details.get('launches', {}).items():
            if deployments.get(account_id, {}).get('launches', {}).get(launch_name) is None:
                pass
            else:
                for region, regional_details in deployments[account_id]['launches'][launch_name].items():
                    if regional_details.get('status') == "AVAILABLE":
                        status = Color("{green}" + regional_details.get('status') + "{/green}")
                    else:
                        status = Color("{red}" + regional_details.get('status') + "{/red}")
                    expected_version = launch.get('version')
                    actual_version = regional_details.get('version')
                    if expected_version == actual_version:
                        actual_version = Color("{green}" + actual_version + "{/green}")
                    else:
                        actual_version = Color("{red}" + actual_version + "{/red}")
                    active = regional_details.get('active')
                    if active:
                        active = Color("{green}" + str(active) + "{/green}")
                    else:
                        active = Color("{orange}" + str(active) + "{/orange}")
                    table.append([
                        account_id,
                        region,
                        launch_name,
                        regional_details.get('portfolio'),
                        regional_details.get('product'),
                        expected_version,
                        actual_version,
                        active,
                        status,
                    ])
    click.echo(AsciiTable(table).table)