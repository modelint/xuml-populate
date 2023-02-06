"""
flow.py – Populate a Flow in PyRAL
"""

import logging
from PyRAL.relvar import Relvar
from typing import TYPE_CHECKING
from class_model_dsl.populate.pop_types import Data_Flow_i, Flow_i

if TYPE_CHECKING:
    from tkinter import Tk


class Flow:
    """
    Create a Flow relation
    """
    _logger = logging.getLogger(__name__)
    _activity_nums = {}

    @classmethod
    def populate(cls, mmdb: 'Tk', domain_name):
        """Constructor"""

        next_flow_id = 1

        # Populate
        Relvar.insert(relvar='Flow', tuples=[
            Flow_i(ID=next_flow_id, Domain=domain_name)
        ])
        Relvar.insert(relvar='Data_Flow', tuples=[
            Data_Flow_i(ID=next_flow_id, Domain=domain_name)
        ])
        next_flow_id += 1

        # Just enough here to support Activity Subsystem population
        # TODO: Add the rest of this subsystem later