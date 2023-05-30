"""
action.py – Populate an action instance in PyRAL
"""

import logging
from PyRAL.relvar import Relvar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tkinter import Tk

class Action:
    """
    Create all relations for an Action
    """
    _logger = logging.getLogger(__name__)

    @classmethod
    def populate(cls, mmdb: 'Tk', anum: str, domain_name: str, aparse):
        """
        Populate the entire Action

        :param anum:
        :param mmdb:
        :param aparse:
        :param domain_name:
        :return:
        """
        agroup_name = type(aparse.action_group).__name__
        # For now we'll just swithc on the action_group name and later wrap all this up
        # into a dictionary of functions of some sort
        if agroup_name == 'Inst_Assignment_a':
            # Process lhs
            lhs = aparse.action_group.lhs
            output_flow = lhs.name.name
            output_type = lhs.exp_type
            # If an explicit type is specified, we must ensure that there is no conflict with the output of the rhs
            # otherwise we apply the output type of the rhs. Either way, we need to process the rhs before proceeding
            # Process rhs
            rhs = aparse.action_group.rhs

            pass
            # Create an action of the appropriate type
        pass
