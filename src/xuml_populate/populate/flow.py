"""
flow.py – Populate a Flow in PyRAL
"""

import logging
from pyral.relvar import Relvar
from pyral.relation import Relation
from typing import TYPE_CHECKING, Optional
from xuml_populate.exceptions.action_exceptions import FlowException
from xuml_populate.populate.mmclass_nt import Data_Flow_i, Flow_i, \
    Multiple_Instance_Flow_i, Single_Instance_Flow_i, Instance_Flow_i, \
    Control_Flow_i, Non_Scalar_Flow_i, Scalar_Flow_i, Table_Flow_i, Labeled_Flow_i, Unlabeled_Flow_i, \
    Tuple_Flow_i, Relation_Flow_i
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content

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
    def lookup_data(cls, fid: str, anum: str, domain: str) -> Flow_ap:
        """
        Given a Data Flow identifier (fid, anum, domain), determine the flow content, tname, and maxmult

        Raise exception if no such Data Flow

        :param domain:
        :param anum:
        :param mmdb:
        :param fid:
        :return: A flow descriptor for the supplied ID
        """
        # First verify that the fid corresponds to some Data Flow instance
        R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
        result = Relation.restrict(cls.mmdb, relation='Data_Flow', restriction=R)
        if not result.body:
            # Either fid not defined or it is a Control Flow
            raise FlowException

        # Is Non Scalar or Scalar Flow?
        R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
        result = Relation.restrict(cls.mmdb, relation='Non_Scalar_Flow', restriction=R)
        if result.body:
            # It is a Non Scalar Flow
            R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
            result = Relation.restrict(cls.mmdb, relation='Instance_Flow', restriction=R)
            if result.body:
                # It's an Instance Flow
                tname = result.body[0]['Type']
                R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
                result = Relation.restrict(cls.mmdb, relation='Multiple_Instance_Flow', restriction=R)
                max_mult = MaxMult.MANY if result.body else MaxMult.ONE
                return Flow_ap(fid=fid, content=Content.INSTANCE, tname=tname, max_mult=max_mult)
            else:
                # Must be a Table Flow
                R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
                result = Relation.restrict(cls.mmdb, relation='Table_Flow', restriction=R)
                tname = result.body[0]['Type']
                R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
                result = Relation.restrict(cls.mmdb, relation='Relation_Flow', restriction=R)
                max_mult = MaxMult.MANY if result.body else MaxMult.ONE
                return Flow_ap(fid=fid, content=Content.TABLE, tname=tname, max_mult=max_mult)
        else:
            # It's a Scalar Flow
            R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
            result = Relation.restrict(cls.mmdb, relation='Scalar_Flow', restriction=R)
            tname = result.body[0]['Type']
            return Flow_ap(fid=fid, content=Content.SCALAR, tname=tname, max_mult=None)

    @classmethod
    def populate_data_flow_by_type(cls, mmdb: 'Tk', label: Optional[str], mm_type: str, activity: str,
                                   domain: str) -> Flow_ap:
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
        cls.mmdb = mmdb
        # For now we distinguish only between class and scalar types
        # Is the type a Class Type?
        R = f"Name:<{mm_type}>, Domain:<{domain}>"
        r_result = Relation.restrict(cls.mmdb, relation='Class', restriction=R)
        if r_result.body:
            # It's a class type, create a multiple instance flow
            content = Content.INSTANCE
            max_mult = MaxMult.MANY
            flow = cls.populate_instance_flow(mmdb, cname=mm_type, activity=activity, domain=domain, label=label)
        else:
            # It's a scalar type
            content = Content.SCALAR
            max_mult = None
            flow = cls.populate_scalar_flow(mmdb, scalar_type=mm_type, activity=activity, domain=domain,
                                               label=label)
        return flow

    @classmethod
    def populate_scalar_flow(cls, mmdb: 'Tk', label: Optional[str], scalar_type: str, activity: str,
                             domain: str) -> Flow_ap:
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
        return Flow_ap(fid=flow_id, content=Content.SCALAR, tname=scalar_type, max_mult=None)

    @classmethod
    def populate_instance_flow(cls, mmdb: 'Tk', cname: str, activity: str, domain: str, label: Optional[str],
                               single: bool = False) -> Flow_ap:
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
            Instance_Flow_i(ID=flow_id, Activity=activity, Domain=domain, Class=cname)
        ])
        if single:
            max_mult = MaxMult.ONE
            Relvar.insert(relvar='Single_Instance_Flow', tuples=[
                Single_Instance_Flow_i(ID=flow_id, Activity=activity, Domain=domain)
            ])
        else:
            max_mult = MaxMult.MANY
            Relvar.insert(relvar='Multiple_Instance_Flow', tuples=[
                Multiple_Instance_Flow_i(ID=flow_id, Activity=activity, Domain=domain)
            ])
        return Flow_ap(fid=flow_id, content=Content.INSTANCE, tname=cname, max_mult=max_mult)

    @classmethod
    def populate_non_scalar_flow(cls) -> str:
        """
        Populate an instance of Non Scalar flow
        """
        fid = cls.populate_data_flow()
        Relvar.insert(relvar='Non_Scalar_Flow', tuples=[
            Non_Scalar_Flow_i(ID=fid, Activity=cls.activity, Domain=cls.domain)
        ])
        return fid

    @classmethod
    def populate_data_flow(cls) -> str:
        """
        """
        fid = cls.populate_flow()
        Relvar.insert(relvar='Data_Flow', tuples=[
            Data_Flow_i(ID=fid, Activity=cls.activity, Domain=cls.domain)
        ])
        return fid

    @classmethod
    def populate_table_flow(cls, mmdb: 'Tk', activity: str, domain: str, tname: str, label: Optional[str],
                            is_tuple: bool = False) -> Flow_ap:
        flow_id = cls.populate_non_scalar_flow()
        Relvar.insert(relvar='Table_Flow', tuples=[
            Table_Flow_i(ID=flow_id, Activity=cls.activity, Domain=cls.domain, Type=tname)
        ])
        if not is_tuple:
            Relvar.insert(relvar='Relation_Flow', tuples=[
                Relation_Flow_i(ID=flow_id, Activity=cls.activity, Domain=cls.domain)
            ])
        else:
            Relvar.insert(relvar='Tuple_Flow', tuples=[
                Tuple_Flow_i(ID=flow_id, Activity=cls.activity, Domain=cls.domain)
            ])
        return Flow_ap(fid=flow_id, content=Content.TABLE, tname=tname,
                       max_mult=MaxMult.ONE if is_tuple else MaxMult.MANY)

    @classmethod
    def populate_flow(cls) -> str:
        """
        Populate Flow instance and optional Label
        """
        # Each activity requires a new flow id counter
        activity_id = f'{cls.domain}:{cls.activity}'  # combine attributes to get id
        if activity_id not in cls.flow_id_ctr.keys():
            cls.flow_id_ctr[activity_id] = 0

        # Populate Flow instance
        cls.flow_id_ctr[activity_id] += 1  # Increment the flow id counter for this activity
        flow_id = f"F{cls.flow_id_ctr[activity_id]}"
        Relvar.insert(relvar='Flow', tuples=[
            Flow_i(ID=flow_id, Activity=cls.activity, Domain=cls.domain)
        ])

        # If a label has been defined, populate it
        if cls.label:
            Relvar.insert(relvar='Labeled_Flow', tuples=[
                Labeled_Flow_i(Name=cls.label, ID=flow_id, Activity=cls.activity, Domain=cls.domain)
            ])
        else:
            Relvar.insert(relvar='Unlabeled_Flow', tuples=[
                Unlabeled_Flow_i(ID=flow_id, Activity=cls.activity, Domain=cls.domain)
            ])

        return flow_id
