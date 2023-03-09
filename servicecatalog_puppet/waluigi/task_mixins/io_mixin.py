#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import logging

import luigi
from luigi import format
from luigi.contrib import s3

from servicecatalog_puppet import config, constants, serialisation_utils


logger = logging.getLogger(constants.PUPPET_LOGGER_NAME)


def escape(input):
    return "".join(x for x in input if x.isalnum() or x in "._- ")


class IOMixin:
    @property
    def drift_token_parameters(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} has cachable_level of TASK but has not implemented drift_token_parameters"
        )

    @property
    def output_location_non_cached(self):
        if self.cachable_level == constants.CACHE_LEVEL_TASK:
            path = f"{escape(self.drift_token_parameters)}/{self.drift_token}"
            # path = self.drift_token
        elif self.cachable_level == constants.CACHE_LEVEL_RUN:
            path = self.run_token
        elif self.cachable_level == constants.CACHE_LEVEL_PERMANENT:
            path = "latest"
        elif self.cachable_level == constants.CACHE_LEVEL_NO_CACHE:
            path = self.run_token
        else:
            raise Exception(f"unknown cachable_level: {self.cachable_level}")

        return f"output/{self.__class__.__name__}/{self.task_reference}/{path}.json"

    @property
    def output_location_cached(self):
        return f"s3://sc-puppet-caching-bucket-{self.puppet_account_id}-{constants.HOME_REGION}/{self.output_location_non_cached}"

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
            return s3.S3Target(self.output_location_cached, format=format.UTF8)
        else:
            return luigi.LocalTarget(
                self.output_location_non_cached, format=luigi.format.Nop
            )

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
