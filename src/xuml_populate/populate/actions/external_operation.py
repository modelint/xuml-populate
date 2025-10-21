"""
external_operation.py – Populate an external operation call
"""
# System
import logging
from typing import Optional, TYPE_CHECKING

# Model Integration
from scrall.parse.visitor import Call_a, Op_a, Supplied_Parameter_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity

from xuml_populate.config import mmdb
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.actions.read_action import ReadAction
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.actions.aparse_types import Boundary_Actions, Flow_ap, MaxMult, ActivityType
from xuml_populate.populate.mmclass_nt import (
    Operation_Call_i, Operation_Call_Parameter_i, Operation_Call_Output_i, Instance_Action_i
)

if __debug__:
    from xuml_populate.utility import print_mmdb

_logger = logging.getLogger(__name__)

tr_ExtOp = "External Operation"

class ExternalOperation:
    """
    Populate all components of an External Service call
    """
    def __init__(self, parse: Op_a, activity: 'Activity'):
        """
        Initialize the data we need to populate a method call

        Args:
            parse: A parsed call or op statement (that resolves to a method invocation)
            activity:  Information about the activity where this action executes
        """
        # Ensure that we are not calling from an instance (not an assigner, for example)
        if not activity.xiflow:
            msg = (f"External operation {parse.op_name} call must originate in a lifecycle or method "
                   f"activity at: {activity.activity_path}")
            _logger.error(msg)
            ActionException(msg)
        self.activity = activity
        self.anum = activity.anum
        self.domain = activity.domain
        self.class_name = activity.xiflow.tname
        self.op_name = parse.op_name
        self.params = parse.supplied_params

        self.action_id = None
        self.signum = None

    def populate(self) -> tuple[str, str, Optional[Flow_ap]]:
        """
        Populate an Operation Call action

        Returns:
            There's only one action here, so the initial_pseudo_state and output actions will just be the id of the method call.
        """
        Transaction.open(db=mmdb, name=tr_ExtOp)
        # Populate the action superclass and obtain our action id
        self.action_id = Action.populate(tr=tr_ExtOp, anum=self.anum, domain=self.domain, action_type="operation call")
        # Insert the Operation Call instance
        Relvar.insert(db=mmdb, tr=tr_ExtOp, relvar='Instance Action', tuples=[
            Instance_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_ExtOp, relvar='Operation Call', tuples=[
            Operation_Call_i(ID=self.action_id, Activity=self.anum, Domain=self.domain, Operation=self.op_name)
        ])

        # Validate Operation Call params (ensure that the call matches the Operation's populated signature
        R = f"Name:<{self.op_name}>, Domain:<{self.domain}>"
        ext_service_sv = 'ext_service_sv'
        ext_service_r = Relation.restrict(db=mmdb, relation='External Service', restriction=R,
                                          svar_name=ext_service_sv)
        if len(ext_service_r.body) != 1:
            msg = f"External operation not defined in: {self.activity.activity_path}"
            _logger.error(msg)
            raise ActionException(msg)
        self.signum = ext_service_r.body[0]['Signature']
        param_r = Relation.semijoin(db=mmdb, rname2='Parameter', attrs={'Signature': 'Signature', 'Domain': 'Domain'})
        sig_params = {t["Name"]: t["Type"] for t in param_r.body}

        # Populate each Parameter specified in the signature with an incoming Data Flow
        from xuml_populate.populate.actions.expressions.scalar_expr import ScalarExpr
        sp_pnames: set[str] = set()
        for sp in self.params:

            # Set the supplied parameter name
            pname = sp.pname
            sp_pnames.add(pname)

            # Resolve the supplied value to a flow or constant value
            sval_name = None
            sval_type = type(sp.sval).__name__
            sval_flow = None
            match sval_type:
                case 'N_a' | 'IN_a':
                    sval_name = sp.sval.name
                case 'INST_PROJ_a':
                    se = ScalarExpr(expr=sp.sval, input_instance_flow=self.activity.xiflow, activity=self.activity)
                    bactions, scalar_flows = se.process()
                    if len(scalar_flows) != 1:
                        msg = f"Type operation output is not a single scalar flow, instead got {scalar_flows}"
                        _logger.error(msg)
                        raise ActionException(msg)
                    sval_flow = scalar_flows[0]
                case '_':
                    pass

            if sval_flow is None:
                # Populate parameter data flows
                if sval_name is not None:
                    # We have either a flow label or an attribute name
                    R = f"Name:<{sval_name}>, Class:<{self.class_name}>, Domain:<{self.domain}>"
                    attr_r = Relation.restrict(db=mmdb, relation="Attribute", restriction=R)
                    if attr_r.body:
                        ra = ReadAction(input_single_instance_flow=self.activity.xiflow,
                                        attrs=(sval_name,), anum=self.anum, domain=self.domain)
                        aid, sflows = ra.populate()
                        sval_flow = sflows[0]
                    else:
                        sval_flows = Flow.find_labeled_scalar_flow(name=sval_name, anum=self.anum, domain=self.domain)
                        sval_flow = sval_flows[0] if sval_flows else None
                        # TODO: Check for case where multiple are returned
                else:
                    msg = f"No input flow found for operation call {self.action_id} input source for param {pname}"
                    _logger.error(msg)
                    raise ActionException(msg)

            # Validate type match
            if sval_flow.tname != sig_params[pname]:
                msg = (f"Supplied parameter flow type for {pname} does not match signature Parameter type "
                       f"{sig_params[pname]}")
                _logger.error(msg)
                raise ActionException  # TODO : Type define mismatch exception

            Relvar.insert(db=mmdb, tr=tr_ExtOp, relvar='Operation Call Parameter', tuples=[
                Operation_Call_Parameter_i(
                    Operation_call=self.action_id, Activity=self.anum, Parameter=pname,
                    Signature=self.signum, Domain=self.domain, Flow=sval_flow.fid)
            ])

        # Populate the Operation Call Output if an output flow is specified
        output_r = Relation.semijoin(db=mmdb, rname1=ext_service_sv, rname2='External Operation Output', attrs={
            'Name': 'Operation', 'Domain': 'Domain'
        })
        sflow = None
        if output_r.body:
            # There is an output defined
            output_scalar = output_r.body[0]['Type']
            flow_name = output_r.body[0]['Name']
            sflow_label = f"_{self.action_id[4:]}_{flow_name}"
            sflow = Flow.populate_scalar_flow(scalar_type=output_scalar, anum=self.anum, domain=self.domain,
                                              label=sflow_label)
            Relvar.insert(db=mmdb, tr=tr_ExtOp, relvar='Operation Call Output', tuples=[
                Operation_Call_Output_i(
                    Operation_call=self.action_id, Activity=self.anum, Domain=self.domain,
                    Operation_name=self.op_name, Flow=sflow.fid)
            ])

        Transaction.execute(db=mmdb, name=tr_ExtOp)

        return self.action_id, self.action_id, sflow
