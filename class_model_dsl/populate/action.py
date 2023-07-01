"""
action.py – Populate an action instance in PyRAL
"""

import logging
from PyRAL.relvar import Relvar
from PyRAL.relation import Relation
from PyRAL.transaction import Transaction
from class_model_dsl.populate.actions.traverse_action import TraverseAction
from class_model_dsl.populate.flow import Flow
from class_model_dsl.populate.actions.instance_assignment import InstanceAssignment
from class_model_dsl.populate.pop_types import Action_i, Traverse_Action_i
from typing import TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from tkinter import Tk

class ActivityType(Enum):
    METHOD = 1
    STATE = 2
    OPERATION = 3

class Action:
    """
    Create all relations for an Action
    """
    _logger = logging.getLogger(__name__)
    next_action_id = {}
    activity_type = None # enum: state, ee, method
    state = None # state name
    operation = None # operation name
    method = None  # method name
    cname = None

    @classmethod
    def populate_method(cls, mmdb: 'Tk', cname: str, method:str, anum: str, domain: str, aparse):
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
        :return:
        """
        cls.activity_type = ActivityType.METHOD
        cls.cname = cname
        cls.method = method
        cls.populate(mmdb, anum, domain, aparse)


    @classmethod
    def populate(cls, mmdb: 'Tk', anum: str, domain: str, aparse):
        """
        Populate an Action
        """
        # Each activity requires a new action counter
        activity_key = f'{domain}:{anum}' # combine attributes to get id
        if activity_key not in cls.next_action_id.keys():
            cls.next_action_id[activity_key] = 0
        cls.next_action_id[activity_key] += 1
        actn_id = f'ACTN{cls.next_action_id[activity_key]}'

        Transaction.open(mmdb) # Traverse Action

        # Populate the Action superclass
        Relvar.insert(relvar='Action', tuples=[
            Action_i(ID=actn_id, Activity=anum, Domain=domain)
        ])

        agroup_name = type(aparse.action_group).__name__
        # For now we'll just switch on the action_group name and later wrap all this up
        # into a dictionary of functions of some sort
        if agroup_name == 'Inst_Assignment_a':
            InstanceAssignment.process(mmdb, actn_id=actn_id, cname=cls.cname, domain=domain,
                                       inst_assign_parse=aparse.action_group)

            # Populate the Traverse Action
            dest_class = None
            # Process lhs
            # Create an output flow for the lhs
            output_flow = lhs.name.name
            output_type = lhs.exp_type
            # If an explicit type is specified, we must ensure that there is no conflict with the output of the rhs
            # otherwise we apply the output type of the rhs. Either way, we need to process the rhs before proceeding

            # Create the instance flow for the lhs
            R = f"Anum:<{anum}>, Domain:<{domain}>"
            r_result = Relation.restrict3(mmdb, relation='Method', restriction=R)
            if not r_result.body:
                return False
            xi_flow = r_result.body[0]['Executing_instance_flow']
            # Process rhs
            components = aparse.action_group.rhs.components
            # A variety of actions may be associated with these components, depends on the component type
            card = aparse.action_group.card

            Relvar.insert(relvar='Traverse_Action', tuples=[
                Traverse_Action_i(ID=actn_id, Activity=anum, Domain=domain, Path=None,
                                  Source_flow=xi_flow, Destination_flow=None)
            ])
            for c in components:
                # if type(c).__name__ == 'N_a':
                # Prefix name as input source
                if type(c).__name__ == 'PATH_a':
                    # Create instance of Path
                    dest_class = TraverseAction.build_path(mmdb, source_class=cls.cname, domain=domain, path=c)

            # Now that we have a destination class, create the LHS instance flow
            # The type of the LHS is either declared explicitly or inferred based on the result of the RHS
            lhs_class_type = lhs.exp_type if not None else dest_class
            Flow.populate_instance_flow(cname=lhs_class_type, activity=anum, domain=domain,
                                        label=lhs.name.name, single=True if card==1 else False)
            # Resolve type of RHS
            # Create an action of the appropriate type
        pass
