"""
flow.py – Populate a Flow in PyRAL
"""

import logging
from PyRAL.relvar import Relvar
from PyRAL.relation import Relation
from typing import TYPE_CHECKING, Optional
from class_model_dsl.populate.pop_types import Data_Flow_i, Flow_i,\
    Multiple_Instance_Flow_i, Single_Instance_Flow_i, Instance_Flow_i,\
    Control_Flow_i, Non_Scalar_Flow_i, Scalar_Flow_i, Table_Flow_i, Label_i

if TYPE_CHECKING:
    from tkinter import Tk

# TODO: Add Table and Control Flow population

class Flow:
    """
    Create a Flow relation
    """
    _logger = logging.getLogger(__name__)
    flow_id_ctr = {}  # Manage flow id numbering per anum:domain

    domain = None
    activity = None
    label = None
    mmdb = None

    @classmethod
    def populate_data_flow_by_type(cls, mmdb: 'Tk', label:Optional[str], mm_type:str, activity:str, domain:str) -> str:
        """
        Populate an instance of Data Flow and determine its subclasses based on the supplied
        Class, Scalar, or Table Type.

        :param mmdb:
        :param label:
        :param mm_type: A Class, Scalar, or Table Type
        :param activity:
        :param domain:
        :return: The generated flow id
        """
        # For now we distinguish only between class and scalar types
        # Is the type a Class Type?
        R = f"Name:<{mm_type}>, Domain:<{domain}>"
        r_result = Relation.restrict3(cls.mmdb, relation='Class_Type', restriction=R)
        if r_result.body:
            # It's a class type, create a multiple instance flow
            flow_id = cls.populate_instance_flow(mmdb, cname=mm_type, activity=activity, domain=domain, label=label)
        else:
            # It's a scalar type
            flow_id = cls.populate_scalar_flow(mmdb, scalar_type=mm_type, activity=activity, domain=domain,
                                               label=label)
        return flow_id

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

        flow_id = cls.populate_data_flow()
        Relvar.insert(relvar='Scalar_Flow', tuples=[
            Scalar_Flow_i(ID=flow_id, Activity=cls.activity, Domain=cls.domain, Type=scalar_type)
        ])
        return flow_id

    @classmethod
    def populate_instance_flow(cls, mmdb: 'Tk', cname:str, activity:str, domain:str, label:Optional[str],
                               single:bool=False) -> str:
        """
        Populate an instance of Scalar flow

        :param mmdb:
        :param label:
        :param cname:
        :param activity:
        :param domain:
        :param single: If true, single otherwise multiple instance flow
        :return: The generated flow id
        """
        # Set all these values so that the superclass populates can find them
        cls.label = label
        cls.domain = domain
        cls.activity = activity
        cls.mmdb = mmdb

        flow_id = cls.populate_non_scalar_flow()
        Relvar.insert(relvar='Instance_Flow', tuples=[
            Instance_Flow_i(ID=flow_id, Activity=activity, Domain=domain, Class_Type=cname)
        ])
        if single:
            Relvar.insert(relvar='Single_Instance_Flow', tuples=[
                Single_Instance_Flow_i(ID=flow_id, Activity=activity, Domain=domain)
            ])
        else:
            Relvar.insert(relvar='Multiple_Instance_Flow', tuples=[
                Multiple_Instance_Flow_i(ID=flow_id, Activity=activity, Domain=domain)
            ])
        return flow_id

    @classmethod
    def populate_non_scalar_flow(cls) -> str:
        """
        Populate an instance of Non Scalar flow
        """
        flow_id = cls.populate_data_flow()
        Relvar.insert(relvar='Non_Scalar_Flow', tuples=[
            Non_Scalar_Flow_i(ID=flow_id, Activity=cls.activity, Domain=cls.domain)
        ])
        return flow_id

    @classmethod
    def populate_data_flow(cls) -> str:
        """
        """
        flow_id = cls.populate_flow()
        Relvar.insert(relvar='Data_Flow', tuples=[
            Data_Flow_i(ID=flow_id, Activity=cls.activity, Domain=cls.domain)
        ])
        return flow_id

    @classmethod
    def populate_flow(cls) -> str:
        """
        Populate Flow instance and optional Label
        """
        # Each activity requires a new flow id counter
        activity_id = f'{cls.domain}:{cls.activity}' # combine attributes to get id
        if activity_id not in cls.flow_id_ctr.keys():
            cls.flow_id_ctr[activity_id] = 0

        # Populate Flow instance
        cls.flow_id_ctr[activity_id] +=1  # Increment the flow id counter for this activity
        flow_id = cls.flow_id_ctr[activity_id]
        Relvar.insert(relvar='Flow', tuples=[
            Flow_i(ID=flow_id, Activity=cls.activity, Domain=cls.domain)
        ])

        # If a label has been defined, populate it
        if cls.label:
            Relvar.insert(relvar='Label', tuples=[
                Label_i(Name=cls.label, Flow=flow_id, Activity=cls.activity, Domain=cls.domain)
            ])

        return flow_id