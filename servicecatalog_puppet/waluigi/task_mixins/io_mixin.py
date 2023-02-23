import logging

import luigi
from luigi import format
from luigi.contrib import s3

from servicecatalog_puppet import config, constants, serialisation_utils


logger = logging.getLogger(constants.PUPPET_LOGGER_NAME)


class IOMixin:
    def get_output_location_path(self):
        if self.cachable_level == constants.CACHE_LEVEL_TASK:
            path = self.task_idempotency_token
        elif self.cachable_level == constants.CACHE_LEVEL_RUN:
            path = self.run_idempotency_token
        elif self.cachable_level == constants.CACHE_LEVEL_PERMANENT:
            path = "latest"
        elif self.cachable_level == constants.CACHE_LEVEL_NO_CACHE:
            path = self.run_idempotency_token
        else:
            raise Exception(f"unknown cachable_level: {self.cachable_level}")
        return f"output/{self.__class__.__name__}/{self.task_reference}/{path}.{self.output_suffix}"

    @property
    def cached_output_location(self):
        path = self.get_output_location_path()
        return f"s3://sc-puppet-caching-bucket-{config.get_puppet_account_id()}-{config.get_home_region(self.puppet_account_id)}/{path}"

    @property
    def output_location(self):
        if self.should_use_caching:
            return self.cached_output_location
        else:
            return self.get_output_location_path()

    @property
    def should_use_caching(self):
        return (
            self.should_use_s3_target_if_caching_is_on and config.is_caching_enabled()
        )

    @property
    def should_use_s3_target_if_caching_is_on(self):
        return self.cachable_level != constants.CACHE_LEVEL_NO_CACHE

    def output(self):
        if self.should_use_caching:
            return s3.S3Target(self.output_location, format=format.UTF8)
        else:
            return luigi.LocalTarget(self.output_location, format=luigi.format.Nop)

    @property
    def output_suffix(self):
        return "json"

    def params_for_results_display(self):
        return {}

    def write_empty_output(self):
        if self.should_use_caching:
            with self.output().open("w") as f:
                f.write("{}")
        else:
            with self.output().open("wb") as f:
                f.write(b"{}")

    def write_output(self, content):
        if self.should_use_caching:
            with self.output().open("w") as f:
                f.write(serialisation_utils.json_dumps(content).decode("utf-8"))
        else:
            with self.output().open("wb") as f:
                f.write(serialisation_utils.json_dumps(content))
