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
    _anum_counters = {}  # A separate counter per domain

    @classmethod
    def init_counter(cls, domain_name: str) -> str:
        # Should refactor this into an Element population numbering method
        if domain_name not in cls._anum_counters:
            cls._anum_counters[domain_name] = 1
        else:
            cls._anum_counters[domain_name] += 1
        return f'A{cls._anum_counters[domain_name]}'

    @classmethod
    def populate_state(cls, mmdb: 'Tk', state: str, state_model: str, domain_name: str) -> str:
        """Constructor"""

        anum = cls.init_counter(domain_name)


        pass

