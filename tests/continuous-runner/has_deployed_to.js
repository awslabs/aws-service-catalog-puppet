const AWS = require('aws-sdk');

'use strict';

module.exports.handler = async (event) => {
    console.log(event);
    const scenario = event.Scenario;
    const newCommitHash = event.newCommitHash;
    const codepipelineExecutionId = event.codepipelineExecutionId;
    console.log(`scenario is ${scenario}, newCommitHash is ${newCommitHash} and codepipelineExecutionId is ${codepipelineExecutionId}`);
    const pipelineName = "servicecatalog-puppet-pipeline";
    var codepipeline = new AWS.CodePipeline();

    const result = await codepipeline.getPipelineExecution(
        {
            pipelineName: pipelineName,
            pipelineExecutionId: codepipelineExecutionId
        }
    ).promise();

    const finishedStates = [
        "Cancelled",
        "Stopped",
        "Succeeded",
        "Superseded",
        "Failed",
    ];

    if (finishedStates.includes(result.pipelineExecution.status)) {
        console.log("pipeline is no longer running, reporting metric");
        const listActionExecutionsResponse = await codepipeline.listActionExecutions(
            {
                pipelineName: pipelineName,
                filter: {
                    pipelineExecutionId: codepipelineExecutionId
                },
            }
        ).promise();
        let executionTime = 0;
        listActionExecutionsResponse.actionExecutionDetails.forEach( listActionExecution => {
            if (listActionExecution.stageName === "Deploy" && listActionExecution.actionName === "Deploy") {
                executionTime = Math.floor(listActionExecution.lastUpdateTime - listActionExecution.startTime);
            }
        });

        var cloudwatch = new AWS.CloudWatch();
        await cloudwatch.putMetricData(
            {
                MetricData: [
                    {
                        MetricName: 'ServiceCatalogPuppetExecutionTime',
                        Dimensions: [
                            {
                                Name: 'Status',
                                Value: result.pipelineExecution.status
                            },
                            {
                                Name: 'Scenario',
                                Value: scenario
                            },
                        ],
                        Timestamp: new Date,
                        Unit: "Seconds",
                        Value: String(executionTime),
                    },
                ],
                Namespace: 'SCT-e2e-testing'
            }
        ).promise()
    }

    return {
        currentStatus: result.pipelineExecution.status,
        newCommitHash: newCommitHash,
        codepipelineExecutionId: codepipelineExecutionId,
        Scenario: scenario,
    };
};
