import logging
import os
import time
from threading import Thread
import traceback

import yaml
from betterboto import client as betterboto_client
from jinja2 import Environment, FileSystemLoader

from servicecatalog_puppet.asset_helpers import resolve_from_site_packages
from servicecatalog_puppet.constants import HOME_REGION_PARAM_NAME, CONFIG_PARAM_NAME, CONFIG_PARAM_NAME_ORG_IAM_ROLE_ARN, TEMPLATES, PREFIX

logger = logging.getLogger()

