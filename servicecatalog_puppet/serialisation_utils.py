#  Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json

import orjson
import yaml

from servicecatalog_puppet import serialisation_utils


class Equals(yaml.YAMLObject):
    yaml_loader = yaml.SafeLoader
    yaml_dumper = yaml.SafeDumper

    yaml_tag = u"!Equals"

    def __init__(self, values):
        self.values = values

    @classmethod
    def from_yaml(cls, constructor, node):
        x = constructor.construct_sequence(node)
        return cls(values=x)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_sequence(cls.yaml_tag, data.values)

    def get_result(self):
        return all(element == self.values[0] for element in self.values)


class Not(yaml.YAMLObject):
    yaml_loader = yaml.SafeLoader
    yaml_dumper = yaml.SafeDumper

    yaml_tag = u"!Not"

    def __init__(self, values):
        self.values = values

    @classmethod
    def from_yaml(cls, constructor, node):
        x = constructor.construct_sequence(node)
        return cls(values=x)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_sequence(cls.yaml_tag, data.values)

    def get_result(self):
        return not self.values[0]


def load(what):
    return yaml.safe_load(what)


def dump(what):
    return yaml.safe_dump(what, default_flow_style=False, width=1000000)


def dump_as_json(input):
    return json.dumps(input, default=str)


def load_as_json(input):
    return serialisation_utils.json_loads(input)


def json_dumps(obj):
    return orjson.dumps(obj, option=orjson.OPT_INDENT_2)


def json_loads(s):
    return orjson.loads(s)


def unwrap(what):
    if hasattr(what, "get_wrapped"):
        return unwrap(what.get_wrapped())

    if isinstance(what, dict):
        thing = dict()
        for k, v in what.items():
            thing[k] = unwrap(v)
        return thing

    if isinstance(what, tuple):
        thing = list()
        for v in what:
            thing.append(unwrap(v))
        return thing

    if isinstance(what, list):
        thing = list()
        for v in what:
            thing.append(unwrap(v))
        return thing

    return what
