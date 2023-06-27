"""
flow.py – Populate a Flow in PyRAL
"""

import logging
from PyRAL.relvar import Relvar
from typing import TYPE_CHECKING, Optional
from class_model_dsl.populate.pop_types import Data_Flow_i, Flow_i

if TYPE_CHECKING:
    from tkinter import Tk


class Flow:
    """
    Create a Flow relation
    """
    _logger = logging.getLogger(__name__)
    _activity_nums = {}

    flow_id = None
    domain = None
    activity = None
    label = None
    mmdb = None

    @classmethod
    def populate_data_flow(cls) -> str:
        """
        """
        pass


    @classmethod
    def populate_instance_flow(cls, mmdb: 'Tk', cname:str, activity:str, domain:str, label:Optional[str]) -> str:
        """
        Populate an instance of Scalar flow

        :param mmdb:
        :param label:
        :param cname:
        :param activity:
        :param domain:
        :return: The generated flow id
        """
        # Set all these values so that the superclass populates can find them
        cls.label = label
        cls.domain = domain
        cls.activity = activity
        cls.mmdb = mmdb

        return ""

    @classmethod
    def populate_scalar_flow(cls, mmdb: 'Tk', label:Optional[str], scalar_type:str, activity:str, domain:str) -> str:
        """
        Populate an instance of Scalar flow

        :param mmdb:
        :param label:
        :param scalar_type:
        :param activity:
        :param domain:
        :return: The generated flow id
        """
        # Set all these values so that the superclass populates can find them
        cls.label = label
        cls.domain = domain
        cls.activity = activity
        cls.mmdb = mmdb

        Transaction.open(mmdb) # Flow
        Transaction.execute() # Flow



    @classmethod
    def populate_flow(cls, mmdb: 'Tk') -> int:
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