# -*- coding=utf-8 -*-

import os
import logging
import tempfile
from typing import Any, Dict

from airflow.models import BaseOperator

from airflow_db2_plugin.hooks.db2_hook import DB2Hook


class DB2ToFileOperator(BaseOperator):

    template_fields = ("sql", "sql_args", "filepath", "schema")

    def __init__(
        self,
        conn_id: str,
        sql: str,
        sql_args: str,
        filepath: str,
        schema: str = None,
        *args,
        **kwargs,
    ):
        super(DB2ToFileOperator, self).__init__(*args, **kwargs)
        self.conn_id = conn_id
        self.sql = sql
        self.sql_args = sql_args
        self.filepath = filepath
        self.schema = schema

    def execute(self, context: Dict[str, Any]) -> str:
        db2_hook = DB2Hook(self.conn_id, schema=self.schema)

        if not isinstance(self.filepath, str):
            # generate temporary if no filepath given
            self.filepath = os.path.join(
                tempfile.gettempdir(), next(tempfile._get_candidate_names()) + ".csv"
            )
            logging.debug(
                f"no filepath given, creating temporary file at {self.filepath!r}"
            )

        statement = self.sql % tuple(self.sql_args.split(","))
        logging.info(
            f"exporting data from executing {statement!r} on "
            f"{db2_hook!r} to {self.filepath!r}"
        )
        db2_hook.export(self.sql % tuple(self.sql_args.split(",")), self.filepath)
        return self.filepath
