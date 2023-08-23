"""
statement.py – Populate all actions in a Scrall statement
"""

import logging
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction
from xuml_populate.populate.actions.traverse_action import TraverseAction
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.instance_assignment import InstanceAssignment
from xuml_populate.populate.actions.table_assignment import TableAssignment
from xuml_populate.populate.mmclass_nt import Action_i, Traverse_Action_i
from typing import TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from tkinter import Tk

class ActivityType(Enum):
    METHOD = 1
    STATE = 2
    OPERATION = 3

class Statement:
    """
    Create all relations for a Statement
    """
    _logger = logging.getLogger(__name__)
    next_action_id = {}
    activity_type = None # enum: state, ee, method
    state = None # state name
    operation = None # operation name
    method = None  # method name
    cname = None
    signum = None
    xi_flow_id = None

    @classmethod
    def populate_method(cls, mmdb: 'Tk', cname: str, method:str, anum: str, domain: str, aparse, scrall_text:str):
        """
        When we populate a method we need to know the class and method name so that we can
        later look up its inputs (executing class and parameter inputs).

        Set the method specific attributes and then passing the remaining parameters along

        :param method:
        :param mmdb:
        :param cname:
        :param anum:
        :param domain:
        :param aparse:
        :param scrall_text:
        """
        cls.activity_type = ActivityType.METHOD
        cls.cname = cname
        cls.method = method

        # Look up signature
        R = f"Method:<{method}>, Class:<{cname}>, Domain:<{domain}>"
        result = Relation.restrict3(mmdb, relation='Method_Signature', restriction=R)
        if not result.body:
            # TODO: raise exception here
            pass
        cls.signum = result.body[0]['SIGnum']

        # Look up xi flow
        R = f"Name:<{method}>, Class:<{cname}>, Domain:<{domain}>"
        result = Relation.restrict3(mmdb, relation='Method', restriction=R)
        if not result.body:
            # TODO: raise exception here
            pass
        cls.xi_flow_id = result.body[0]['Executing_instance_flow']
        activity_path = f"{domain}:{cname}:{method}.mtd"
        cls.populate(mmdb, anum, domain, aparse, activity_path, scrall_text)

    @classmethod
    def populate(cls, mmdb: 'Tk', anum: str, domain: str, aparse, activity_path:str, scrall_text:str):
        """
        Populate a Statement
        """
        agroup_name = type(aparse.action_group).__name__
        # For now we'll just switch on the action_group name and later wrap all this up
        # into a dictionary of functions of some sort
        match agroup_name:
            case 'Inst_Assignment_a':
                InstanceAssignment.process(mmdb, anum=anum, cname=cls.cname, domain=domain,
                                           inst_assign_parse=aparse.action_group, xi_flow_id=cls.xi_flow_id,
                                           activity_path=activity_path, scrall_text=scrall_text)
            case 'Table_Assignment_a':
                TableAssignment.process(mmdb, anum=anum, cname=cls.cname, domain=domain,
                                        table_assign_parse=aparse.action_group, xi_flow_id=cls.xi_flow_id,
                                        activity_path=activity_path, scrall_text=scrall_text)

