"""
instance_assignment.py – Break an instance set generator into one or more components
"""

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.exceptions.action_exceptions import AssignZeroOneInstanceHasMultiple
from xuml_populate.populate.actions.aparse_types import InstanceFlow_ap, MaxMult

from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

from collections import namedtuple

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

    input_instance_flow = None  # The instance flow feeding the next component on the RHS
    assign_zero_one = None  # Does assignment operator limit to a zero or one instance selection?

    @classmethod
    def process(cls, mmdb: 'Tk', anum: str, cname: str, domain: str, inst_assign_parse,
                xi_flow_id: str, activity_path: str, scrall_text: str):
        """
        Given a parsed instance set expression, populate each component action
        and return the resultant Class Type name

        We'll need an initial flow and we'll need to create intermediate instance flows to connect the components.
        The final output flow must be an instance flow. The associated Class Type determines the type of the
        assignment which must match any explicit type.

        :param mmdb: The metamodel db
        :param cname: The class (for an operation it is the proxy class)
        :param domain: In this domain
        :param anum: The Activity Number
        :param inst_assign_parse: A parsed instance assignment
        :param xi_flow_id: The ID of the executing instance flow (the instance executing this activity)
        :param activity_path: Human readable path to the activity for error reporting
        :param scrall_text: The parsed scrall text for error reporting
        """
        lhs = inst_assign_parse.lhs
        assign_zero_one = True if inst_assign_parse.card == '1' else False
        rhs = inst_assign_parse.rhs
        # The executing instance is by nature a single instance flow
        xi_instance_flow = InstanceFlow_ap(fid=xi_flow_id, ctype=cname, max_mult=MaxMult.ONE)

        # Process the instance set expression in the RHS and obtain the generated instance flow
        iset_instance_flow = InstanceSet.process(mmdb, anum=anum, input_instance_flow=xi_instance_flow,
                                                 iset_components=rhs.components, domain=domain,
                                                 activity_path=activity_path, scrall_text=scrall_text)

        # Process LHS after all components have been processed
        if assign_zero_one and iset_instance_flow.max_mult == MaxMult.ONE:
            raise AssignZeroOneInstanceHasMultiple(path=activity_path, text=scrall_text, x=inst_assign_parse.X)
        output_flow_label = lhs.name.name
        if lhs.exp_type and lhs.exp_type != iset_instance_flow.ctype:
            # Raise assignment type mismatch exception
            pass

        # Populate the LHS assignment labeled flow
        Transaction.open(mmdb)  # LHS labeled instance flow
        assigned_flow = Flow.populate_instance_flow(mmdb, cname=iset_instance_flow.ctype, activity=anum,
                                                    domain=domain, label=output_flow_label, single=assign_zero_one)

        _logger.info(f"INSERT Instance Flow (assignment): ["
                     f"{domain}:{iset_instance_flow.ctype}:{activity_path.split(':')[-1]}"
                     f":{output_flow_label}:{assigned_flow}]")
        Transaction.execute()  # LHS labeled instance flow
