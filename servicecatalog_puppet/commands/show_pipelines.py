#  Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import datetime
import json
from servicecatalog_puppet import serialisation_utils

import click
import terminaltables
from betterboto import client as betterboto_client

from servicecatalog_puppet import constants
from servicecatalog_puppet import utils

result_look_up = dict(Failed="red", Succeeded="green")
trigger_look_up = dict(StartPipelineExecution="Manual Full Run")


def show_pipelines(format):
    pipelines_to_check = dict(core={"servicecatalog-puppet-pipeline": dict()},)

    fake_date = datetime.datetime.now()
    with betterboto_client.ClientContextManager("codepipeline") as codepipeline:
        for type, pipelines in pipelines_to_check.items():
            for pipeline_name, pipeline_details in pipelines.items():
                try:
                    executions = codepipeline.list_pipeline_executions(
                        pipelineName=pipeline_name, maxResults=5
                    ).get("pipelineExecutionSummaries", [])
                except codepipeline.exceptions.PipelineNotFoundException as e:
                    executions = []

                if len(executions) > 0:
                    last_execution = executions[0]
                else:
                    last_execution = dict(
                        status="N/A",
                        lastUpdateTime=fake_date,
                        startTime=fake_date,
                        sourceRevisions=[dict(revisionId="N/A", revisionSummary="N/A")],
                    )

                trend = list()
                for execution in executions:
                    trend.append(
                        dict(
                            start_time=execution.get("startTime", fake_date),
                            duration=execution.get("lastUpdateTime", fake_date)
                            - execution.get("startTime", fake_date),
                            status=execution.get("status"),
                            trigger=trigger_look_up.get(
                                execution.get("trigger").get("triggerType"), "N/A"
                            ),
                        )
                    )

                source_revisions = last_execution.get("sourceRevisions")
                if len(source_revisions) == 0:
                    source_revisions.append(
                        dict(revisionId="N/A", revisionSummary="N/A")
                    )

                pipelines[pipeline_name] = {
                    "name": pipeline_name,
                    "trigger": trigger_look_up.get(
                        last_execution.get("trigger").get("triggerType"), "N/A"
                    ),
                    "pipeline_execution_id": last_execution.get(
                        "pipelineExecutionId", "N/A"
                    ),
                    "start_time": last_execution.get("startTime", fake_date),
                    "status": last_execution.get("status"),
                    "revision_id": source_revisions[0].get("revisionId", "N/A"),
                    "revision_summary": source_revisions[0].get(
                        "revisionSummary", "N/A"
                    ),
                    "duration": last_execution.get("lastUpdateTime")
                    - last_execution.get("startTime"),
                    "trend": trend,
                }

    if format == "json":
        click.echo(json.dumps(pipelines_to_check, indent=4, default=str))
    elif format == "table":
        table_data = [
            [
                "Type",
                "Name",
                "Trigger",
                "Execution Id",
                "Start Time",
                "Status",
                "Last Commit Id",
                "Last Commit Message",
                "Duration",
                "Trend",
            ],
        ]
        for type, pipelines in pipelines_to_check.items():
            for pipeline_name, pipeline_details in pipelines.items():
                table_data.append(
                    [
                        type,
                        pipeline_details.get("name"),
                        pipeline_details.get("trigger"),
                        pipeline_details.get("pipeline_execution_id"),
                        pipeline_details.get("start_time"),
                        pipeline_details.get("status"),
                        pipeline_details.get("revision_id"),
                        pipeline_details.get("revision_summary"),
                        pipeline_details.get("duration"),
                        ", ".join(
                            [
                                f"{a.get('status')}"
                                for a in pipeline_details.get("trend", [])
                            ]
                        ),
                    ]
                )
        table = terminaltables.AsciiTable(table_data)
        click.echo(table.table)
    elif format == "html":
        content = ""
        content += "<table class='pipes'>"
        content += "    <tr>"
        content += "        <th>Name</th>"
        content += "        <th>Trigger</th>"
        content += "        <th>Status</th>"
        content += "        <th>Start Time</th>"
        content += "        <th>Revision Id</th>"
        content += "        <th>Revision Summary</th>"
        content += "        <th>Duration</th>"
        content += "        <th>Trend</th>"
        content += "    </tr>"

        for type, pipelines in pipelines_to_check.items():
            for pipeline_name, pipeline_details in pipelines.items():
                result = result_look_up.get(pipeline_details.get("status"), "amber")
                trend = "<br /> ".join(
                    [
                        f"{a.get('trigger')}:{a.get('status')[0]}"
                        for a in pipeline_details.get("trend", [])
                    ]
                )
                content += f"    <tr class='{result}'>"
                content += f"        <td>{pipeline_details.get('name')}</td>"
                content += f"        <td>{pipeline_details.get('status')}</td>"
                content += f"        <td>{pipeline_details.get('trigger')}</td>"
                content += f"        <td>{pipeline_details.get('start_time')}</td>"
                content += f"        <td>{pipeline_details.get('revision_id')}</td>"
                content += (
                    f"        <td>{pipeline_details.get('revision_summary')}</td>"
                )
                content += f"        <td>{pipeline_details.get('duration')}</td>"
                content += f"        <td>{trend}</td>"
                content += "    </tr>"

        content += "</table>"
        template = utils.ENV.get_template(constants.STATIC_HTML_PAGE)
        rendered = template.render(title="Factory Pipelines", content=content)
        click.echo(rendered)
