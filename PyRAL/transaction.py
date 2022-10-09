"""
transaction.py -- Database transaction
"""
import logging
from database import db


class Transaction:
    """
    A TclRAL transaction

    """
    _statements = []
    _cmd = ""
    _logger = logging.getLogger(__name__)
    _result = None
    _schema = []

    @classmethod
    def build_schema(cls):
        """
        Executes a set of Relvars and Constraints to define a database schema
        :return:
        """
        pass

    @classmethod
    def update_schema(cls, statement: str):
        cls._schema.append(statement)

    @classmethod
    def execute(cls):
        """
        Executes all statements as a TclRAL relvar eval transaction
        :return:  The TclRal success/fail result
        """
        cls._cmd = f"relvar eval " + "{\n    " + '\n    '.join(cls._statements) + "\n}"
        cls._logger.info(f"Executing transaction:")
        cls._logger.info(cls._cmd)
        cls._result = db.eval(cls._cmd)
        cls._logger.info(f"With result: [{cls._result}]")

    @classmethod
    def add_statement(cls, statement: str):
        cls._statements.append(statement)