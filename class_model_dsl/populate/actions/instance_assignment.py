"""
instance_assignment.py – Break an instance set generator into one or more components
"""

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from class_model_dsl.populate.actions.traverse_action import TraverseAction

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)

class InstanceAssignment:
    """
    Break down a Scrall instance assignment statement into action semantics and populate them

    The lhs (left hand side) will be a labeled Instance Flow. It may or may not have an explicit Class Type.
    The card (cardinality) is either 1c or Mc (one or many conditional). It determines whether the lhs Instance
    Flow is Single or Multiple.

    The rhs (right hand side) is an expression that outputs an instance set of some Class Type. If the lhs is
    explicitly typed, we throw an exception if the rhs and lhs types do not match.

    For now we limit the expression to a chain of the following components:
        * create action
        * traversal action
        * instance flow
        * method or operation output of Class Type
        * selection output

    We say 'chain' since the output of one can feed into the input of the next yielding a final output at the end
    of the chain. It is this final output that determines the type (or type conflict) with the lhs Instance Flow

    We say 'for now' because this chain does not yet take into account instance set operations (add, subtract, union,
    etc). The Scrall syntax will later be udpated to accommodate such expressions.
    """

    @classmethod
    def process(cls, mmdb: 'Tk', actn_id:str, cname:str, domain:str, inst_assign_parse):
        """
        Given a parsed instance set expression, populate each component action
        and return the resultant Class Type name

        We start by setting the assumed ctype to the cname (class of the instance/ee executing this action).
        The ctype is updated as we process each component of the instance set expression until we reach the
        final output ctype which determines the lhs Class Type or any conflict.

        :param cname: The class (for an operation it is the proxy class)
        :param domain: In this domain
        :param mmdb: The metamodel db
        :param actn_id: The ID for this action
        :param inst_assign_parse: A parsed instance assignment
        """
        lhs = inst_assign_parse.action_group.lhs
        card = inst_assign_parse.action_group.card
        rhs = inst_assign_parse.action_group.rhs
        ctype = cname # Initialize with the instance/ee class
        for c in rhs.components:
            if type(c).__name__ == 'PATH_a':
                # Process the path to create the traverse action and obtain the resultant Class Type name
                ctype = TraverseAction.build_path(mmdb, source_class=cname, domain=domain, path=c)
            pass
        pass
