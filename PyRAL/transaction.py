"""
transaction.py -- Database transaction
"""
import logging
from PyRAL.pyral_exceptions import IncompleteTransactionPending
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter

class Transaction:
    """
    A TclRAL transaction

    """
    _statements = None
    _cmd = ""
    _logger = logging.getLogger(__name__)
    _result = None
    _schema = []
    _db = None

    @classmethod
    def open(cls, db):
        """
        Starts a new empty transaction by ensuring that there are no statements

        :return:
        """
        cls._db = db
        if cls._statements:
            cls._logger.error(f"New transaction opened before closing previous.")
            raise IncompleteTransactionPending
        cls._statements = []
        return

    @classmethod
    def append_statement(cls, statement: str):
        """
        Adds a statement to the list of pending statements in the open transaction.

        :param statement:  Statement to be appended
        """
        cls._statements.append(statement)
        return

    @classmethod
    def execute(cls):
        """
        Executes all statements as a TclRAL relvar eval transaction
        :return:  The TclRal success/fail result
        """
        cls._cmd = f"relvar eval " + "{\n    " + '\n    '.join(cls._statements) + "\n}"
        cls._logger.info(f"Executing transaction:")
        cls._logger.info(cls._cmd)
        cls._result = cls._db.eval(cls._cmd)
        cls._statements = None  # The statements have been executed
        cls._logger.info(f"With result: [{cls._result}]")

