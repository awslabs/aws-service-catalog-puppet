import luigi

from servicecatalog_puppet import config, constants
from servicecatalog_puppet.workflow.dependencies import tasks


class CreateEventBusTask(tasks.TaskWithReferenceAndCommonParameters):
    organization = luigi.Parameter()
    event_bus_name = luigi.Parameter()
    role_name = luigi.Parameter()
    role_path = luigi.Parameter()
    role_managed_policy_arns = luigi.ListParameter()

    cachable_level = constants.CACHE_LEVEL_RUN

    def params_for_results_display(self):
        return {
            "task_reference": self.task_reference,
            "region": self.region,
            "account_id": self.account_id,
        }

    def run(self):
        # TODO move to troposphere
        template = f"""Description: event bus template for c7n created by service catalog puppet
Resources:
  eventbus:
    Properties:
      Name: {self.event_bus_name}
    Type: AWS::Events::EventBus
  eventbuspolicy:
    Properties:
      Condition:
        Key: aws:PrincipalOrgID
        Type: StringEquals
        Value: {self.organization}
      Action: events:PutEvents
      Principal: '*'
      StatementId: OrganizationAccounts
    Type: AWS::Events::EventBusPolicy"""
        with self.spoke_regional_client("cloudformation") as cloudformation:
            cloudformation.create_or_update(
                ShouldUseChangeSets=False,
                StackName="servicecatalog-puppet-c7n-eventbus",
                TemplateBody=template,
                NotificationARNs=[
                    f"arn:{config.get_partition()}:sns:{self.region}:{self.puppet_account_id}:servicecatalog-puppet-cloudformation-regional-events"
                ]
                if self.should_use_sns
                else [],
                ShouldDeleteRollbackComplete=self.should_delete_rollback_complete_stacks,
                Tags=self.initialiser_stack_tags,
            )
        self.write_output(
            dict(
                c7n_account_id=self.account_id,
                event_bus_name=self.event_bus_name,
                role_name=self.role_name,
                role_path=self.role_path,
                role_managed_policy_arns=self.role_managed_policy_arns,
            )
        )
