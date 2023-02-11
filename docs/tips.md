## export all env vars from a codebuild build id in your local
aws codebuild batch-get-builds --ids servicecatalog-puppet-deploy-in-spoke:0568a289-ebb6-4189-9bc0-5d6a4ff4879d | jq -r '.builds[0].environment.environmentVariables[]| "export \(.name)=\"\(.value)\""' 

