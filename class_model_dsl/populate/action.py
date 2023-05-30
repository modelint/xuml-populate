"""
action.py – Populate an action instance in PyRAL
"""

import logging
from PyRAL.relvar import Relvar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tkinter import Tk

class Action:
    """
    Create all relations for an Action
    """
    _logger = logging.getLogger(__name__)

    @classmethod
    def populate(cls, mmdb: 'Tk', aparse):
        """
        Populate the entire Action

        :param mmdb:
        :param aparse:
        :return:
        """
        pass
