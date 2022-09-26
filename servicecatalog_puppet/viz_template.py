CONTENT = """<!DOCTYPE HTML>
<html>
<head>
    <title>Timeline</title>

    <style type="text/css">
        body, html {{
            font-family: sans-serif;
        }}
        .success {{
            color: white !important;
        }}
        .failure {{
            color: red !important;
        }}
        .AppSectionTask {{
            background-color: #ffdd00 !important;
        }}
        .AssertionsSectionTask {{
            background-color: #00ffe1 !important;
        }}
        .CodeBuildRunsSectionTask {{
            background-color: rgb(125, 41, 175) !important;
        }}
        .GenericScheduleRunDeployInSpokeTask {{
            background-color: #646164 !important;
        }}
        .GetCloudFormationTemplateFromS3 {{
            background-color: #646164 !important;
        }}
        .GetSSMParamIndividuallyTask {{
            background-color: #9b82fa !important;
        }}
        .GetSSMParamTask {{
            background-color: #9b82fa !important;
        }}
        .LambdaInvocationsSectionTask {{
            background-color: #a6e391 !important;
        }}
        .LaunchSectionTask {{
            background-color: #ff7300 !important;
        }}
        .ProvisionStackTask {{
            background-color: #f397a3 !important;
        }}
        .ServiceControlPoliciesSectionTask {{
            background-color: #2cadf6 !important;
        }}
        .SimulatePolicysSectionTask {{
            background-color: #8c6e00 !important;
        }}
        .SpokeLocalPortfolioSectionTask {{
            background-color: #005586 !important;
        }}
        .StackSectionTask {{
            background-color: #f397a3 !important;
        }}
        .StackTask {{
            background-color: #f397a3 !important;
        }}
        .TagPoliciesSectionTask {{
            background-color: #2cadf6 !important;
        }}
        .WorkspaceSectionTask {{
            background-color: #137206 !important;
        }}

    </style>

    <script src="https://visjs.github.io/vis-timeline/standalone/umd/vis-timeline-graph2d.min.js" rel="script"></script>
    <link href="https://visjs.github.io/vis-timeline/styles/vis-timeline-graph2d.min.css" rel="stylesheet"
          type="text/css"/>
</head>
<body>
<div id="visualization"></div>

<script type="text/javascript">
    // DOM element where the Timeline will be attached
    var container = document.getElementById('visualization');

    // Create a DataSet (allows two way data-binding)
    var items = new vis.DataSet({DATASET});
    
    var groups = new vis.DataSet({GROUPS});

    // Configuration for the Timeline
    var options = {{
    
        start: "{START}",
        end: "{END}",

        height: 800,

        selectable: false,

        showTooltips: true,

        tooltip: {{
            followMouse: true,
        }},

        timeAxis: {{scale: 'second', step: 10}},

        format: {{
            minorLabels: function (date, scale, step) {{
                return date.format("ss");
            }},
            majorLabels: function (date, scale, step) {{
                return date.format("HH:mm:ss");
            }}
        }},

    }};

    // Create a Timeline    
    var timeline = new vis.Timeline({PARAMS});
</script>
</body>
</html>"""
