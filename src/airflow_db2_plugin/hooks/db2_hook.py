# -*- coding=utf-8 -*-

import csv
import logging
import contextlib
from typing import List, Generator

import pyodbc
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from airflow.hooks.dbapi_hook import DbApiHook


class DB2Hook(DbApiHook):

    conn_namespace = "db2"
    conn_driver = "pyodbc400"

    def __init__(self, *args, **kwargs):
        super(DB2Hook, self).__init__(*args, **kwargs)
        self.connection = self.get_connection(getattr(self, self.conn_name_attr))
        self.database = kwargs.pop("database", getattr(self.connection, "schema", None))
        self.schema = kwargs.pop(
            "schema", self.connection.extra_dejson.get("schema", "")
        )

    def get_conn(self):
        logging.info(f"establishing connection to db2 at {self.connection.host!r}")
        return pyodbc.connect(self.get_uri())

    def get_uri(self) -> str:
        host = self.connection.host
        if self.connection.port is not None:
            host = f"{host}:{self.connection.port}"
        if len(self.schema) > 0:
            schema = f",{self.schema}"
        return (
            f"{self.conn_namespace}+{self.conn_driver}://"
            f"{self.connection.login}:{self.connection.password}"
            f"@{host}/{self.database};DBQ=QGPL{schema};DEBUG=65536"
        )

    def get_sqlalchemy_sessionmaker(self):
        engine = self.get_sqlalchemy_engine()
        logging.info(
            f"buliding sqlalchemy sessionmaker instance with engine {engine!r}"
        )
        return sessionmaker(bind=engine)

    def get_sqlalchemy_session(self):
        logging.info(f"building sqlalchemy session")
        return self.get_sqlalchemy_sessionmaker()()

    @contextlib.contextmanager
    def sqlalchemy_session(self):
        session = self.get_sqlalchemy_session()
        logging.info(f"entering sqlalchemy session context with session {session!r}")
        try:
            yield session
            session.commit()
        except Exception:
            logging.exception(f"exception occured during session {session!r}")
            session.rollback()
            raise
        finally:
            logging.info(f"closing sqlalchemy session {session!r}")
            session.close()

    def query(
        self, sql: str, parameters: List[str], include_headers: bool = True
    ) -> Generator:
        if parameters is None:
            parameters = []

        if len(parameters) > 0:
            sql = sql % tuple(parameters)

        logging.info(f"executing query {sql!r}")
        sql_text = sqlalchemy.text(sql)
        with self.get_sqlalchemy_session() as session:
            results = session.execute(sql_text)
            if include_headers:
                yield results.keys()
            for row in results:
                yield row

    def export(
        self,
        sql: str,
        filepath: str,
        parameters: List[str],
        include_headers: bool = True,
        **kwargs,
    ) -> str:
        logging.info(f"writing results of sql {sql!r} to {filepath!r}")
        with open(filepath, "w") as fp:
            writer = csv.writer(fp)
            for result in self.query(
                sql, parameters=parameters, include_headers=include_headers, **kwargs
            ):
                writer.writerow(result)
        return filepath
