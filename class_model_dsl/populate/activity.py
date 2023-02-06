"""
activity.py – Populate an activity instance in PyRAL
"""

import logging
from PyRAL.relvar import Relvar
from typing import TYPE_CHECKING
from class_model_dsl.populate.pop_types import Activity_i, Asynchronous_Activity_i,\
    State_Activity_i, Signature_i, Parameter_i

if TYPE_CHECKING:
    from tkinter import Tk

_signum_counters = {} # A separate counter per domain

class Activity:
    """
    Create a State Model relation
    """
    _logger = logging.getLogger(__name__)
    _avnum_counters = {}  # A separate counter per domain

    @classmethod
    def populate(cls, mmdb: 'Tk', record):
        """Constructor"""
        pass

