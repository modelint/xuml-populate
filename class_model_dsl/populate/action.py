"""
action.py – Populate an action instance in PyRAL
"""

import logging
from PyRAL.relvar import Relvar
from class_model_dsl.populate.actions.traverse_action import TraverseAction
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tkinter import Tk

class Action:
    """
    Create all relations for an Action
    """
    _logger = logging.getLogger(__name__)
    id_ctr = 1

    @classmethod
    def populate(cls, mmdb: 'Tk', cname: str, anum: str, domain_name: str, aparse):
        """
        Populate the entire Action

        :param cname:
        :param anum:
        :param mmdb:
        :param aparse:
        :param domain_name:
        :return:
        """
        agroup_name = type(aparse.action_group).__name__
        # For now we'll just switch on the action_group name and later wrap all this up
        # into a dictionary of functions of some sort
        if agroup_name == 'Inst_Assignment_a':
            # Process lhs
            lhs = aparse.action_group.lhs
            # Create an output flow for the lhs
            output_flow = lhs.name.name
            output_type = lhs.exp_type
            # If an explicit type is specified, we must ensure that there is no conflict with the output of the rhs
            # otherwise we apply the output type of the rhs. Either way, we need to process the rhs before proceeding
            # Process rhs
            components = aparse.action_group.rhs.components
            # A variety of actions may be associated with these components, depends on the component type
            card = aparse.action_group.card
            for c in components:
                # if type(c).__name__ == 'N_a':
                # Prefix name as input source
                if type(c).__name__ == 'PATH_a':
                    TraverseAction.build_path(mmdb, source_class=cname, domain=domain_name, path=c)
                    # We need to create a traverse action that takes an input instance flow and produces an output instance flow
                    # Create instance of Path
                    first_hop = True
                    for hop in c.hops:
                        # if first hop and hop is an rnum
                        # Create hop, look up the relationship
                        pass

            pass
            # Create an action of the appropriate type
        pass
