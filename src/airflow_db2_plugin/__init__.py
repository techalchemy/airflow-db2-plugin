# -*- coding=utf-8 -*-
# Copyright (c) 2019 Dan Ryan

import os
import sys

from airflow.plugins_manager import AirflowPlugin

from airflow_db2_plugin.hooks.db2_hook import DB2Hook
from airflow_db2_plugin.operators.db2_to_file_operator import DB2ToFileOperator

# insert vendor directory into syspath
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "vendor"))


class Db2Plugin(AirflowPlugin):
    """Apache Airflow DB2 Plugin."""

    name = "db2_plugin"
    hooks = [DB2Hook]
    operators = [DB2ToFileOperator]
    executors = []
    macros = []
    admin_views = []
    flask_blueprints = []
    menu_links = []
