import luigi
from servicecatalog_puppet.workflow import tasks


class GetCloudFormationTemplateFromS3(tasks.PuppetTask):
    bucket = luigi.Parameter()
    key = luigi.Parameter()
    version_id = luigi.Parameter()

    def params_for_results_display(self):
        return {
            "bucket": self.bucket,
            "key": self.key,
            "version_id": self.version_id,
        }

    def run(self):
        with self.client("s3") as s3:
            p = dict(Bucket=self.bucket, Key=self.key, )
            if self.version_id != "":
                p['VersionId'] = self.version_id
            response = s3.get_object(**p)
            self.write_output(
                response.get("Body").read().decode("utf8"), skip_json_dump=True
            )
