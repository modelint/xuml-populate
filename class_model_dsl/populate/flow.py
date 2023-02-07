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
    def populate(cls, mmdb: 'Tk', anum, domain_name, flow_type: str) -> int:
        """Constructor"""

        activity_id = f'{domain_name}:{anum}' # combine attributes to get id
        if activity_id not in cls._activity_nums.keys():
            cls._activity_nums[activity_id] = 1

        # Populate
        fid = cls._activity_nums[activity_id]
        Relvar.insert(relvar='Flow', tuples=[
            Flow_i(ID=fid, Activity=anum, Domain=domain_name)
        ])
        Relvar.insert(relvar='Data_Flow', tuples=[
            Data_Flow_i(ID=fid, Activity=anum, Domain=domain_name, Type=flow_type)
        ])
        # Increment the flow id counter for this activity
        cls._activity_nums[activity_id] +=1

        return fid

        # Just enough here to support Activity Subsystem population
        # TODO: Add the rest of this subsystem later