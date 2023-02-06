"""
signature.py – Populate a Signature in PyRAL
"""

import logging
from PyRAL.relvar import Relvar
from typing import TYPE_CHECKING
from class_model_dsl.populate.pop_types import Signature_i, State_Signature_i

if TYPE_CHECKING:
    from tkinter import Tk


class Signature:
    """
    Create a Signature relation with a unique id
    """
    _logger = logging.getLogger(__name__)
    _signum_counters = {} # A separate counter per domain

    @classmethod
    def populate(cls, mmdb: 'Tk', domain_name) -> str:
        """Constructor"""

        if domain_name not in cls._signum_counters.keys():
            # Initialize a new domain signature number counter
            cls._signum_counters[domain_name] = 1

        # Populate
        signum = f'SIG{cls._signum_counters[domain_name]}' # SIG1, SIG2, ...
        cls._signum_counters[domain_name] += 1
        Relvar.insert(relvar='Signature', tuples=[
            Signature_i(SIGnum=signum, Domain=domain_name)
        ])
        return signum

        # Just enough here to support Activity Subsystem population
        # TODO: Add the rest of this subsystem later