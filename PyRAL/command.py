"""
command.py – Execute a TclRAL command
"""

import logging
from tkinter import Tk, TclError

class Command:
    """
    A relational variable (table)

    TclRAL does not support spaces in names, but PyRAL accepts space delimited names.
    But each space delimiter will be replaced with an underscore delimiter before submitting to TclRAL
    """
    _logger = logging.getLogger(__name__)

    @classmethod
    def execute(cls, tclral: Tk, cmd: str, log: bool=True) -> str:
        """
        Executes a TclRAL command via the supplied session and returns TclRAL's string result.

        :param tclral: The TclRAL session
        :param cmd: A TclRAL command string
        :param log:  If false, the result will not be logged. Useful when no meaningful result is expected
        :return: The string received as a result of executing the command
        """
        cls._logger.info(f"cmd: {cmd}")
        try:
            result = tclral.eval(cmd)
        except TclError as e:
            cls._logger.exception(e)
            raise

        if log:
            cls._logger.info(f"result: {result}")
        return result