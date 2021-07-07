const AWS = require('aws-sdk');
const yaml = require('js-yaml');

'use strict';

console.log("Loading function");

module.exports.handler = async (event) => {
    console.log("Starting function");

    const scenario = event['Scenario'];
    let shouldTerminate = false;
    if (event['ShouldTerminate'] != undefined) {
        shouldTerminate = String(event['ShouldTerminate']).toUpperCase() == "TRUE";
    }

    const branchName = 'ml_demo';
    const repositoryName = 'ServiceCatalogPuppet';
    const filePath = 'manifest.yaml';

    var codecommit = new AWS.CodeCommit();
    var codepipeline = new AWS.CodePipeline();


    const response = await codecommit.getFile(
        {
            filePath: `scenarios/${scenario}.yaml`,
            repositoryName: repositoryName,
            commitSpecifier: branchName
        }
    ).promise()
    const newContent = Buffer.from(response.fileContent, 'base64').toString() + "\n" + "#" + new Date;

    const putResult = await codecommit.putFile(
        {
            branchName: branchName,
            fileContent: newContent,
            filePath: filePath,
            repositoryName: repositoryName,
            parentCommitId: response.commitId,
            commitMessage: `Setting to ${scenario}`
        }
    ).promise();
    const newCommitHash = putResult.commitId;

    let codepipelineExecutionId = "";
    while (codepipelineExecutionId == "") {
        await new Promise(resolve => setTimeout(resolve, 3000));
        let pipelineExections = await codepipeline.listPipelineExecutions({pipelineName: "servicecatalog-puppet-pipeline"}).promise();
        pipelineExections.pipelineExecutionSummaries.forEach(execution => {
            execution.sourceRevisions.forEach(sourceRevision => {
                if (sourceRevision.actionName == "Source") {
                    if (sourceRevision.revisionId == newCommitHash) {
                        codepipelineExecutionId = execution.pipelineExecutionId;
                    }
                }
            });
        });
    }

    if (shouldTerminate) {
        await codepipeline.stopPipelineExecution(
            {
                pipelineExecutionId: codepipelineExecutionId,
                pipelineName: "servicecatalog-puppet-pipeline",
                abandon: true,
                reason: 'Resetting'
            }
        ).promise();
    }

    return {
        newCommitHash: newCommitHash,
        codepipelineExecutionId: codepipelineExecutionId
    };
};
