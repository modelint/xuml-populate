"""
instance_assignment.py – Break an instance set generator into one or more components
"""

import logging
from typing import Set, Dict, List, Optional
from xuml_populate.config import mmdb
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Labeled_Flow_i
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.exceptions.action_exceptions import AssignZeroOneInstanceHasMultiple
from xuml_populate.populate.actions.aparse_types import (Flow_ap, MaxMult, Content, Activity_ap, Boundary_Actions,
                                                         Labeled_Flow)
from scrall.parse.visitor import Inst_Assignment_a

from pyral.transaction import Transaction
from pyral.relation import Relation  # For debugging
from pyral.relvar import Relvar

_logger = logging.getLogger(__name__)

# Transactions
tr_Migrate = "Migrate to Label"

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

    assign_zero_one = None  # Does assignment operator limit to a zero or one instance selection?

    @classmethod
    def process(cls, activity_data: Activity_ap, inst_assign: Inst_Assignment_a,
                case_name: str, case_outputs: Set[Labeled_Flow]) -> Boundary_Actions:
        """
        Given a parsed instance set expression, populate each component action
        and return the resultant Class Type name

        We'll need an initial flow and we'll need to create intermediate instance flows to connect the components.
        The final output flow must be an instance flow. The associated Class Type determines the type of the
        assignment which must match any explicit type.

        :param case_outputs:
        :param case_name:
        :param inst_assign: The instance assignment statement parse
        :param activity_data: The enveloping anum
        :param case_prefix:
        """
        lhs = inst_assign.lhs
        assign_zero_one = True if inst_assign.card == '1' else False
        rhs = inst_assign.rhs
        # The executing instance is by nature a single instance flow
        xi_instance_flow = Flow_ap(fid=activity_data.xiflow, content=Content.INSTANCE, tname=activity_data.cname,
                                   max_mult=MaxMult.ONE)

        # Process the instance set expression in the RHS and obtain the generated instance flow
        initial_aid, final_aid, iset_instance_flow = InstanceSet.process(input_instance_flow=xi_instance_flow,
                                                                         iset_components=rhs.components,
                                                                         activity_data=activity_data)

        # Process LHS after all components have been processed
        if assign_zero_one and iset_instance_flow.max_mult == MaxMult.ONE:
            raise AssignZeroOneInstanceHasMultiple(path=activity_data.activity_path, text=activity_data.scrall_text,
                                                   x=inst_assign.X)

        case_prefix = '' if not case_name else f"{case_name}_"
        output_flow_label = case_prefix + lhs.name.name
        if case_name:
            case_outputs.add(Labeled_Flow(label=output_flow_label, flow=iset_instance_flow))
        if lhs.exp_type and lhs.exp_type != iset_instance_flow.tname:
            # Raise assignment type mismatch exception
            pass

        # Migrate the RHS output to a labeled flow using the output flow label
        Transaction.open(mmdb, tr_Migrate)  # LHS labeled instance flow

        # Delete the Unlabeled flow
        Relvar.deleteone(mmdb, tr=tr_Migrate, relvar_name="Unlabeled_Flow",
                         tid={"ID": iset_instance_flow.fid, "Activity": activity_data.anum,
                              "Domain": activity_data.domain})
        # Insert the labeled flow
        Relvar.insert(mmdb, tr=tr_Migrate, relvar='Labeled_Flow', tuples=[
            Labeled_Flow_i(ID=iset_instance_flow.fid, Activity=activity_data.anum, Domain=activity_data.domain,
                           Name=output_flow_label)
        ])

        Transaction.execute(mmdb, tr_Migrate)  # LHS labeled instance flow
        pass

        return Boundary_Actions(ain={initial_aid}, aout={final_aid})
