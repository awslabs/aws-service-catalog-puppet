#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import troposphere as t
from troposphere import s3
from troposphere import sns
from troposphere import ssm


def get_template(version: str, default_region_value) -> t.Template:
    description = f"""Bootstrap template used to bootstrap a region of ServiceCatalog-Puppet master
{{"version": "{version}", "framework": "servicecatalog-puppet", "role": "bootstrap-master-region"}}"""

    template = t.Template(Description=description)

    version_parameter = template.add_parameter(
        t.Parameter("Version", Default=version, Type="String")
    )
    default_region_value_parameter = template.add_parameter(
        t.Parameter("DefaultRegionValue", Default=default_region_value, Type="String")
    )

    template.add_resource(
        ssm.Parameter(
            "DefaultRegionParam",
            Name="/servicecatalog-puppet/home-region",
            Type="String",
            Value=t.Ref(default_region_value_parameter),
            Tags={"ServiceCatalogPuppet:Actor": "Framework"},
        )
    )
    version_ssm_parameter = template.add_resource(
        ssm.Parameter(
            "Param",
            Name="service-catalog-puppet-regional-version",
            Type="String",
            Value=t.Ref(version_parameter),
            Tags={"ServiceCatalogPuppet:Actor": "Framework"},
        )
    )

    template.add_resource(
        s3.Bucket(
            "PipelineArtifactBucket",
            BucketName=t.Sub(
                "sc-puppet-pipeline-artifacts-${AWS::AccountId}-${AWS::Region}"
            ),
            VersioningConfiguration=s3.VersioningConfiguration(Status="Enabled"),
            BucketEncryption=s3.BucketEncryption(
                ServerSideEncryptionConfiguration=[
                    s3.ServerSideEncryptionRule(
                        ServerSideEncryptionByDefault=s3.ServerSideEncryptionByDefault(
                            SSEAlgorithm="AES256"
                        )
                    )
                ]
            ),
            PublicAccessBlockConfiguration=s3.PublicAccessBlockConfiguration(
                BlockPublicAcls=True,
                BlockPublicPolicy=True,
                IgnorePublicAcls=True,
                RestrictPublicBuckets=True,
            ),
            Tags=t.Tags({"ServiceCatalogPuppet:Actor": "Framework"}),
        )
    )

    regional_product_topic = template.add_resource(
        sns.Topic(
            "RegionalProductTopic",
            DisplayName="servicecatalog-puppet-cloudformation-regional-events",
            TopicName="servicecatalog-puppet-cloudformation-regional-events",
            Subscription=[
                sns.Subscription(
                    Endpoint=t.Sub(
                        "arn:${AWS::Partition}:sqs:${DefaultRegionValue}:${AWS::AccountId}:servicecatalog-puppet-cloudformation-events"
                    ),
                    Protocol="sqs",
                )
            ],
        ),
    )

    template.add_output(
        t.Output("Version", Value=t.GetAtt(version_ssm_parameter, "Value"))
    )
    template.add_output(
        t.Output("RegionalProductTopic", Value=t.Ref(regional_product_topic))
    )

    return template
