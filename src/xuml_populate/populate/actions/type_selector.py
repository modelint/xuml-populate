"""
type_selector.py – Process a Type Selector action
"""
# System
import logging
from typing import Optional, TYPE_CHECKING

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.config import mmdb
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.action import Action
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.actions.aparse_types import ActivityAP, Boundary_Actions, Flow_ap
from xuml_populate.populate.mmclass_nt import Type_Action_i, Type_Operation_i, Selector_i

if __debug__:
    from xuml_populate.utility import print_mmdb

_logger = logging.getLogger(__name__)

tr_Selector = "Type Selector"

class TypeSelector:
    """
    Type Selector Action
    """

    def __init__(self, scalar: str, value: str, activity: 'Activity'):
        """
        Gather the information necessary to populate a Type Selector Action

        Args:
            scalar: A value is selected from this scalar set
            value: The name of the selected value
            activity:  The enclosing activity
        """
        self.value = value
        self.scalar = scalar
        self.activity = activity
        self.anum = activity.anum
        self.domain = activity.domain

        self.action_id = None
        self.sflow_out = None

    def populate(self) -> tuple[str, str, Flow_ap]:
        """

        Returns:
            This action as the input and output boundary action and the Scalar flow with the selected value
        """
        # Open transaction to populate the Type Selector Action
        Transaction.open(db=mmdb, name=tr_Selector)

        # Populate the action superclass and obtain our action id
        self.action_id = Action.populate(tr=tr_Selector, anum=self.anum, domain=self.domain, action_type="type action")

        # The scalar name and the selected value
        label = f"_{self.scalar}_{self.value}"

        # Populate the output scalar flow (but don't use the generated label)
        self.sflow_out = Flow.populate_scalar_flow(scalar_type=self.scalar, anum=self.anum,
                                                   domain=self.domain, label=label, activity_tr=tr_Selector)

        # Insert the Type Operation Instance providing the input flow scalar, since that's what we're operating on
        Relvar.insert(db=mmdb, tr=tr_Selector, relvar='Type Action', tuples=[
            Type_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain, Scalar=self.scalar,
                          Output_flow=self.sflow_out.fid)
        ])

        Relvar.insert(db=mmdb, tr=tr_Selector, relvar='Selector', tuples=[
            Selector_i(ID=self.action_id, Activity=self.anum, Domain=self.domain, Value=self.value)
        ])

        Transaction.execute(db=mmdb, name=tr_Selector)
        return self.action_id, self.action_id, self.sflow_out
