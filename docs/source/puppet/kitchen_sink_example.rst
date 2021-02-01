Kitchen Sink Example
====================

Here is an example manifest showing how to use the capabilities of the tools:

.. code-block:: yaml

    accounts:
      # defining an account
      - account_id: &service_catalog_tools_account '234982635846243'
        name: 'service_catalog_tools_account'
        default_region: &default_region eu-west-1
        regions_enabled: &regions_enabled
          - eu-west-1
          - eu-west-2
          - eu-west-3
          - us-east-1
          - us-east-2
          - us-west-1
          - us-west-2
        tags:
          - &outype_foundational outype:foundational
          - &ou_sharedservices ou:sharedservices
          - &partition_eu partition:eu
          - &partition_us partition:us
          - &role_hub role:hub
          - &role_service_catalog_tools role:service_catalog_tools
          - &team_ccoe team:ccoe

      - account_id: '9832654846594385'
        name: 'org-manager'
        default_region: us-east-1
        regions_enabled:
          - us-east-1
        tags:
          # using yaml anchors and aliases from above
          - *outype_foundational
          - *ou_sharedservices
          - *partition_us
          - *role_hub
          - &role_org_manager role:org_manager
          - *team_ccoe

      # defining each account in the OU
      - ou: '/workloads/test'
        name: 'workloads-test'
        default_region: *default_region
        regions_enabled: *regions_enabled
        tags:
          - &outype_additional outype:additional
          - &outype_workloads outype:workloads
          - &outype_test outype:test
          - *partition_us
          - *partition_eu
          - &role_spoke role:spoke
        # excluding an account managed by another team
        exclude:
          accounts:
            - "07632469093733"

      # this is a test account but contains PCI data as it is used for load testing and needs real data
      - account_id: '665532578041'
        name: '665532578041'
        # add the tag
        append:
          tags:
            - &score_pci scope:pci

      # this was a test account but is now the active directory account and we cannot move it to the correct ou
      - account_id: '30972093754'
        name: 'active-directory'
        # overwrite the tags
        overwrite:
          tags:
            - *outype_foundational
            - *ou_sharedservices
            - *partition_us
            - *partition_eu
            - *role_hub

    # define some global parameters for provisioning products in launches below
    parameters:
      # Whenever a product has a parameter the framework will use the parameters specified in the accounts section first,
      # then the launch itself and then finally the global
      ServiceCatalogToolsAccountId:
        default: *service_catalog_tools_account

      # the framework will execute the function get_accounts_for_path with the args / and then use the result for the value
      # of this parameter
      AllAccountIds:
        macro:
          method: get_accounts_for_path
          args: /


    # define some mappings that can be used as parameters for launches.  mappings allow us to define groups of parameters
    # just like cloudformation does
    mappings:
      InternetGatewayDeviceAMI:
        us-east-1:
          "ami": "ami-15f77f867"
        us-west-1:
          "ami": "ami-0bdb82235"
        eu-west-1:
          "ami": "ami-16506cd98"

    # actions are wrappers around codebuild projects.  they allow you to run the project and only continue exection
    # should the project be successful
    actions:
      ping-on-prem-host:
        type: codebuild
        project_name: &ping_on_prem_host ping-on-prem-host
        account_id: *service_catalog_tools_account
        region: 'eu-west-1'
        parameters:
          HOST_TO_PING:
            default: 192.168.1.2


    launches:
      # provision v1 of account-bootstrap-shared-org-bootstrap from demo-central-it-team-portfolio into the role_org_manager
      # account
      account-bootstrap-shared-org-bootstrap:
        portfolio: demo-central-it-team-portfolio
        product: account-bootstrap-shared-org-bootstrap
        version: v1
        parameters:
          # Use some parameters for the provisioning
          GovernanceAtScaleAccountFactoryAccountBootstrapSharedBootstrapperOrgIAMRoleName:
            default: AccountBootstrapSharedBootstrapperOrgIAMRoleName
          GovernanceAtScaleAccountFactoryIAMRolePath:
            default: /AccountFactoryIAMRolePath/
          OrganizationAccountAccessRole:
            default: OrganizationAccountAccessRole
        deploy_to:
          tags:
            # deploy only to the default region - which can be a different region per account
            - regions: default_region
              tag: *role_org_manager
        # Store the output from the provisioned product / cloudformation stack in SSM (in the service catalog tools account)
        outputs:
          ssm:
            - param_name: &AssumableRoleArnInRootAccountForBootstrapping /governance-at-scale-account-factory/account-bootstrap-shared-org-bootstrap/AssumableRoleArnInRootAccountForBootstrapping
              stack_output: AssumableRoleArnInRootAccountForBootstrapping

      account-bootstrap-shared:
        portfolio: demo-central-it-team-portfolio
        product: account-bootstrap-shared
        version: v2
        parameters:
          AssumableRoleArnInRootAccountForBootstrapping:
            # use a parameter from SSM (in the service catalog tools account)
            ssm:
              name: *AssumableRoleArnInRootAccountForBootstrapping
          GovernanceAtScaleAccountFactoryAccountBootstrapSharedBootstrapperIAMRoleName:
            default: AccountBootstrapSharedBootstrapperIAMRoleName
          GovernanceAtScaleAccountFactoryAccountBootstrapSharedCustomResourceIAMRoleName:
            default: AccountBootstrapSharedCustomResourceIAMRoleName
          GovernanceAtScaleAccountFactoryIAMRolePath:
            default: /AccountFactoryIAMRolePath/
        # only provision this if account-bootstrap-shared-org-bootstrap provisions correctly
        depends_on:
          - account-bootstrap-shared-org-bootstrap
        outputs:
          ssm:
            - param_name: &GovernanceAtScaleAccountFactoryBootstrapperProjectCustomResourceArn /governance-at-scale-account-factory/account-bootstrap-shared/GovernanceAtScaleAccountFactoryBootstrapperProjectCustomResourceArn
              stack_output: GovernanceAtScaleAccountFactoryBootstrapperProjectCustomResourceArn
        deploy_to:
          tags:
            - regions: default_region
              tag: *role_service_catalog_tools

      internet-gateway:
        portfolio: networking
        product: internet-gateway
        version: v3
        deploy_to:
          tags:
            # regions can also be a list
            - regions:
                - us-east-1
                - us-west-1
                - eu-west-1
              tag: *role_spoke
        parameters:
          AMI:
            # use a mapping as a parameter. when provisioning occurs AWS::Region is replaced with the region being
            # provisioned so you can create region specified parameters in the manifest file, you can also use
            # AWS::AccountId to create account specific parameters in the manifest file
            mapping: [InternetGatewayDeviceAMI, AWS::Region, ami]

      vpc:
        portfolio: networking
        product: vpc
        version: v8
        # before provisioning this product into the specified accounts run the pre_action.  If that project fails this
        # launch will not be provisioned
        pre_actions:
          - name: *ping_on_prem_host
        deploy_to:
          tags:
            - regions:
                - us-east-1
                - us-west-1
                - eu-west-1
              tag: *role_spoke
        parameters:
          NetworkType:
            ssm:
              # when the framework is getting the ssm parameter (in the service catalog tools account) you can use
              # ${AWS::AccountId} and ${AWS::Region} in the name to build out a name dynamically allowing you to use
              # SSM parameter store as a data store for the configuration of each account
              name: /networking/vpc/account-parameters/${AWS::AccountId}/${AWS::Region}/NetworkType
          CIDR:
            ssm:
              name: /networking/vpc/account-parameters/${AWS::AccountId}/${AWS::Region}/CIDR
        outputs:
          ssm:
            # You can also use ${AWS::AccountId} and ${AWS::Region} in the output parameter name
            - param_name: /networking/vpc/account-parameters/${AWS::AccountId}/${AWS::Region}/VPCId
              stack_output: VPCId

      remove-default-vpc-lambda:
        portfolio: networking
        product: remove-default-vpc-lambda
        version: v3
        parameters:
          RemoveDefaultVPCFunctionName:
            default: &RemoveDefaultVPCFunctionName RemoveDefaultVPC
        deploy_to:
          tags:
            - regions: *default_region
              tag: *service_catalog_tools_account


    lambda-invocations:
      # this lambda is executed in the service catalog tools account for each region of each account defined in the
      # invoke_for.  The values of account_id and region are available as parameters to the lambda.
      remove-default-vpc:
        function_name: *RemoveDefaultVPCFunctionName
        qualifier: $LATEST
        invocation_type: Event
        # wait until the lambda is provisioned as part of the launch
        depends_on:
          - name: remove-default-vpc-lambda
            type: launch
        invoke_for:
          tags:
            - regions:
                - us-east-1
                - us-west-1
                - eu-west-1
              tag: *role_spoke


    spoke-local-portfolios:
      networking-self-service:
        portfolio: networking-self-service
        # import the product and not copy it
        product_generation_method: import
        associations:
          - arn:aws:iam::${AWS::AccountId}:role/ServiceCatalogConsumer
        constraints:
          launch:
            - product: account-vending-account-creation-shared
              roles:
                - arn:aws:iam::${AWS::AccountId}:role/ServiceCatalogProvisioner
        deploy_to:
          tags:
            - tag: *role_spoke
              regions: default_region


