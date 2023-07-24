"""
statement.py – Populate all actions in a Scrall statement
"""

import logging
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction
from class_model_dsl.populate.actions.traverse_action import TraverseAction
from class_model_dsl.populate.flow import Flow
from class_model_dsl.populate.actions.instance_assignment import InstanceAssignment
from class_model_dsl.populate.actions.table_assignment import TableAssignment
from class_model_dsl.populate.pop_types import Action_i, Traverse_Action_i
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
                pass

            # # Populate the Traverse Statement
            # dest_class = None
            # # Process lhs
            # # Create an output flow for the lhs
            # output_flow = lhs.name.name
            # output_type = lhs.exp_type
            # # If an explicit type is specified, we must ensure that there is no conflict with the output of the rhs
            # # otherwise we apply the output type of the rhs. Either way, we need to process the rhs before proceeding
            #
            # # Create the instance flow for the lhs
            # R = f"Anum:<{anum}>, Domain:<{domain}>"
            # r_result = Relation.restrict3(mmdb, relation='Method', restriction=R)
            # if not r_result.body:
            #     return False
            # input_instance_flow = r_result.body[0]['Executing_instance_flow']
            # # Process rhs
            # components = aparse.action_group.rhs.components
            # # A variety of actions may be associated with these components, depends on the component type
            # card = aparse.action_group.card
            #
            # Relvar.insert(relvar='Traverse_Action', tuples=[
            #     Traverse_Action_i(ID=actn_id, Activity=anum, Domain=domain, Path=None,
            #                       Source_flow=input_instance_flow, Destination_flow=None)
            # ])
            # for c in components:
            #     # if type(c).__name__ == 'N_a':
            #     # Prefix name as input source
            #     if type(c).__name__ == 'PATH_a':
            #         # Create instance of Path
            #         dest_class = TraverseAction.build_path(mmdb, source_class=cls.cname, domain=domain, path=c)
            #
            # # Now that we have a destination class, create the LHS instance flow
            # # The type of the LHS is either declared explicitly or inferred based on the result of the RHS
            # lhs_class_type = lhs.exp_type if not None else dest_class
            # Flow.populate_instance_flow(cname=lhs_class_type, activity=anum, domain=domain,
            #                             label=lhs.name.name, single=True if card==1 else False)
            # # Resolve type of RHS
            # # Create an action of the appropriate type
        pass
