"""
type_action.py – Process a Type Action
"""
# System
import logging
from typing import Optional

# Model Integration
from scrall.parse.visitor import Supplied_Parameter_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
from xuml_populate.utility import print_mmdb
from xuml_populate.config import mmdb
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.action import Action
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.actions.aparse_types import ActivityAP, Boundary_Actions, Flow_ap
from xuml_populate.populate.mmclass_nt import Type_Action_i, Type_Operation_i, Selector_i

_logger = logging.getLogger(__name__)

tr_Type = "Type Action"

class TypeAction:
    """
    Populate a Type Action
    """

    def __init__(self, op_name: str, anum: str, domain: str, input_flow: Optional[Flow_ap] = None,
                 params: Optional[Supplied_Parameter_a] = None):
        """
        Initialize and populate

        Args:
            op_name:  The name of a type operation or a selected value
            anum:  The method's activity number
            domain: The name of the domain
            input_flow:  A Scalar Flow providing input to the Type Operation Action, none if this is selector op
            params: An optional parse expression with a set of parameters
        """
        self.name = op_name
        self.anum = anum
        self.domain = domain
        self.input_flow = input_flow  # If none, this is a selector operation

        self.action_id = None
        self.sflow_out = None
        self.default_label = None  # Use this label generated below if the user has not specified their own

    def populate(self) -> tuple[str, str, Flow_ap]:
        """

        Returns:
            Initial action, final action, output scalar flow
        """
        # Open transaction to populate the Type Operation Action
        Transaction.open(db=mmdb, name=tr_Type)

        # Populate the action superclass and obtain our action id
        self.action_id = Action.populate(tr=tr_Type, anum=self.anum, domain=self.domain, action_type="type action")

        # Construct a label for the output scalar flow we need to populate for either a type or selector operation
        # This is just a default label that will be superceded by any user specified label by the caller of this
        # action, an assigment statement, for example.
        if self.input_flow:
            # If it is labeled, we can copy that label into the suffix
            R = f"ID:<{self.input_flow.fid}>, Activity:<{self.anum}>, Domain:<{self.domain}>"
            labeled_flow_r = Relation.restrict(db=mmdb, relation="Labeled Flow", restriction=R)
            suffix = self.action_id[:4]  # Just take the number at the end
            if labeled_flow_r.body:
                # Op name and input label if it is labeled, otherwise, use action number
                suffix = labeled_flow_r.body[0]["Name"]
            self.default_label = f"_{self.name}_{suffix}"
        else:
            # The scalar name and the selected value
            self.default_label = f"_{self.input_flow.tname}_{self.name}"

        # Populate the output scalar flow (but don't use the generated label)
        self.sflow_out = Flow.populate_scalar_flow(scalar_type=self.input_flow.tname, anum=self.anum,
                                                   domain=self.domain, activity_tr=tr_Type)

        # Insert the Type Operation Instance providing the input flow scalar, since that's what we're operating on
        Relvar.insert(db=mmdb, tr=tr_Type, relvar='Type Action', tuples=[
            Type_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain, Scalar=self.input_flow.tname,
                          Output_flow=self.sflow_out.fid)
        ])

        if self.input_flow:
            Relvar.insert(db=mmdb, tr=tr_Type, relvar='Type Operation', tuples=[
                Type_Operation_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                                 Name=self.name, Input_flow=self.input_flow.fid)
            ])
        else:
            Relvar.insert(db=mmdb, tr=tr_Type, relvar='Selector', tuples=[
                Selector_i(ID=self.action_id, Activity=self.anum, Domain=self.domain, Value=self.name)
            ])

        Transaction.execute(db=mmdb, name=tr_Type)
        return self.action_id, self.action_id, self.sflow_out

