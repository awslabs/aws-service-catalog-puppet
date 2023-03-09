#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import luigi
import troposphere as t
from troposphere import events

from servicecatalog_puppet import config, constants
from servicecatalog_puppet.workflow.dependencies import tasks


c7nTrailBucket = "c7nTrailBucket"


class ForwardEventsForRegionTask(tasks.TaskWithReferenceAndCommonParameters):
    c7n_account_id = luigi.Parameter()
    custodian_region = luigi.Parameter()
    cachable_level = constants.CACHE_LEVEL_RUN

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "region": self.region,
            "account_id": self.account_id,
        }

    def run(self):
        tpl = t.Template()
        tpl.description = (
            "event forwarder template for c7n created by service catalog puppet"
        )
        tpl.add_resource(
            events.Rule(
                "ForwardAll",
                Description="Forward all events for c7n to do its job",
                EventPattern={"account": [self.account_id],},
                State="ENABLED",
                Targets=[
                    events.Target(
                        Arn=t.Sub(
                            "arn:${AWS::Partition}:events:"
                            + self.custodian_region
                            + ":"
                            + self.c7n_account_id
                            + ":event-bus/default"
                        ),
                        Id="CloudCustodianHubEventBusArn",
                        RoleArn=t.Sub(
                            "arn:${AWS::Partition}:iam::${AWS::AccountId}:role/servicecatalog-puppet/c7n/c7nEventForwarder"
                        ),
                    )
                ],
            )
        )
        template = tpl.to_yaml()
        with self.spoke_regional_client("cloudformation") as cloudformation:
            cloudformation.create_or_update(
                Capabilities=["CAPABILITY_NAMED_IAM"],
                ShouldUseChangeSets=False,
                StackName="servicecatalog-puppet-c7n-eventforwarding-region",
                TemplateBody=template,
                NotificationARNs=[
                    f"arn:{config.get_partition()}:sns:{self.region}:{self.puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events"
                ]
                if self.should_use_sns
                else [],
                ShouldDeleteRollbackComplete=self.should_delete_rollback_complete_stacks,
                Tags=self.initialiser_stack_tags,
            )
        self.write_empty_output()
