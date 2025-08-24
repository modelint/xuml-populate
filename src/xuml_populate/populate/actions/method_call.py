"""
method_call.py – Process a call action
"""
# System
import logging
from typing import Optional, TYPE_CHECKING

# Model Integration
from scrall.parse.visitor import Call_a, Op_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.utility import print_mmdb
from xuml_populate.populate.actions.expressions.scalar_expr import ScalarExpr
from xuml_populate.config import mmdb
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.actions.read_action import ReadAction
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.actions.aparse_types import Boundary_Actions, Flow_ap, MaxMult
from xuml_populate.populate.mmclass_nt import (Method_Call_i, Method_Call_Parameter_i, Method_Call_Output_i,
                                               Instance_Action_i)

_logger = logging.getLogger(__name__)

tr_Call = "Method Call"

class MethodCall:
    """
    Populate all components of a Method Call action and any other
    actions required by the parse
    """
    tr_MethodCallOutput = "Method Call Output"
    method_call_transaction_open: bool = False

    def __init__(self, method_name: str, method_anum: str, caller_flow: Flow_ap, parse: Call_a | Op_a,
                 activity: 'Activity'):
        """
        Initialize the data we need to populate a method call

        Args:
            method_name:  The name of the method to be called
            method_anum:  The method's activity number
            caller_flow:  A single instance flow providing the target instance of the method call
            parse: A parsed call or op statement (that resolves to a method invocation)
            activity:  Information about the activity where this action executes
        """
        self.method_name = method_name
        self.method_anum = method_anum
        self.parse = parse
        # The Scrall grammar indicates that the last element in the components list must be an operation
        self.op_parse = self.parse.call.components[-1] if type(parse).__name__ == "Call_a" else parse
        self.activity = activity
        self.caller_flow = caller_flow
        self.action_id = None
        self.anum = self.activity.anum
        self.domain = self.activity.domain

    @classmethod
    def complete_output_transaction(cls):
        if cls.method_call_transaction_open:
            Transaction.execute(db=mmdb, name=cls.tr_MethodCallOutput)

    def process(self) -> tuple[str, str, Flow_ap]:
        """
        Populate a Method Call action

        Returns:
            There's only one action here, so the initial and output actions will just be the id of the method call.
        """
        # Open transaction to populate the Method Call Action and all required Method Call Parameters
        Transaction.open(db=mmdb, name=tr_Call)
        # Populate the action superclass and obtain our action id
        self.action_id = Action.populate(tr=tr_Call, anum=self.anum, domain=self.domain, action_type="method call")
        # Insert the Method Call instance
        Relvar.insert(db=mmdb, tr=tr_Call, relvar='Instance Action', tuples=[
            Instance_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Call, relvar='Method Call', tuples=[
            Method_Call_i(ID=self.action_id, Activity=self.anum, Domain=self.domain, Method=self.method_anum,
                          Instance_flow=self.caller_flow.fid)
        ])

        # Validate Method Call params (ensure that the call matches the Method's populated signature
        R = f"Anum:<{self.method_anum}>, Domain:<{self.domain}>"
        target_method = Relation.restrict(db=mmdb, relation='Method', restriction=R, svar_name="target_method_sv")
        if len(target_method.body) != 1:
            msg = f"Method call: {self.activity.activity_path} has no target method in mmdb"
            _logger.error(msg)
            raise ActionException(msg)
        target_method_anum = target_method.body[0]["Anum"]
        target_method_sig_r = Relation.semijoin(db=mmdb, rname2='Method Signature',
                                                attrs={'Name': 'Method', 'Domain': 'Domain'})
        # IMPORTANT:
        # We need the signature of the method we are calling (not the signature of the activity calling the method)
        target_method_signum = target_method_sig_r.body[0]['SIGnum']
        param_r = Relation.semijoin(db=mmdb, rname2='Parameter', attrs={'SIGnum': 'Signature', 'Domain': 'Domain'})
        sig_params = {t["Name"]: t["Type"] for t in param_r.body}

        # Populate each Parameter specified in the Method's signature with an incoming Data Flow
        sp_pnames: set[str] = set()
        for sp in self.op_parse.supplied_params:

            # Set the supplied parameter name
            pname = sp.pname
            sp_pnames.add(pname)

            # Resolve the supplied value to a flow or constant value
            sval_name = None
            sval_type = type(sp.sval).__name__
            sval_flow = None
            match sval_type:
                case 'N_a':
                    sval_name = sp.sval.name
                case 'INST_PROJ_a':
                    se = ScalarExpr(expr=sp.sval, input_instance_flow=self.caller_flow, activity=self.activity)
                    bactions, scalar_flows = se.process()
                    if len(scalar_flows) != 1:
                        msg = f"Type operation output is not a single scalar flow, instead got {scalar_flows}"
                        _logger.error(msg)
                        raise ActionException(msg)
                    sval_flow = scalar_flows[0]
                case '_':
                    pass

            # Populate parameter data flows
            if sval_name is not None:
                # We have either a flow label or an attribute name
                R = f"Name:<{sval_name}>, Class:<{self.caller_flow.tname}>, Domain:<{self.domain}>"
                attr_r = Relation.restrict(db=mmdb, relation="Attribute", restriction=R)
                if attr_r.body:
                    ra = ReadAction(input_single_instance_flow=self.caller_flow,
                                    attrs=(sval_name,), anum=self.anum, domain=self.domain)
                    aid, sflows = ra.populate()
                    sval_flow = sflows[0]
                else:
                    sval_flow = Flow.find_labeled_scalar_flow(name=sval_name, anum=self.anum, domain=self.domain)
            else:
                msg = f"Cannot find method call {self.action_id} input source for param {pname}"
                _logger.error(msg)
                raise ActionException(msg)

            if sval_flow is None:
                msg = f"No input flow found for method call {self.action_id} input source for param {pname}"
                _logger.error(msg)
                raise ActionException(msg)

            # Validate type match
            if sval_flow.tname != sig_params[pname]:
                msg = (f"Supplied parameter flow type for {pname} does not match signature Parameter type "
                       f"{sig_params[pname]}")
                _logger.error(msg)
                raise ActionException  # TODO : Type define mismatch exception

            Relvar.insert(db=mmdb, tr=tr_Call, relvar='Method Call Parameter', tuples=[
                Method_Call_Parameter_i(Method_call=self.action_id, Activity=self.anum, Parameter=pname,
                                        Signature=target_method_signum, Domain=self.domain, Flow=sval_flow.fid)
            ])

        # Validate match between set of supplied params and the Method Signature Parameters
        if sp_pnames != set(sig_params.keys()):
            msg = (f"Supplied parameter names [{sp_pnames}] does not match the signature {sig_params} of: "
                   f"Method {self.caller_flow.tname}.{self.method_name}")
            _logger.error(msg)
            ActionException(msg)

        # Create an output flow in this activity compatible with the output of the target method, if any

        method_call_output_flow = None
        target_method_output_type = self.activity.domain_method_output_types[target_method_anum]
        if target_method_output_type is not None:
            method_call_output_flow = None
            # Determine the kind of Data Flow output by the target method
            # Instance flow if the type name is a class
            type_name = target_method_output_type.name
            R = f"Name:<{type_name}>, Domain:<{self.domain}>"
            type_rv = "type_rv" # relational variable to retain type superclass instance for later semijoins
            type_r = Relation.restrict(db=mmdb, relation="Type", restriction=R, svar_name=type_rv)
            if not type_r.body:
                # No matching type found in mmdb
                msg = f"Method signature output type [{type_name}] not in metamodel"
                _logger.error(msg)
                raise ActionException
            # Is the type a class?
            class_r = Relation.semijoin(db=mmdb, rname1=type_rv, rname2="Class")
            if class_r.body:
                # Populate an instance flow for this class using the specified multiplicity, if any
                # Single only if a value (1) was specified for mult, it would be None otherwise
                single = bool(target_method_output_type.mult)
                method_call_output_flow = Flow.populate_instance_flow(activity_tr=tr_Call, cname=type_name,
                                                                      anum=self.anum, domain=self.domain, single=single)
            else:
                # Popualte a sclaar flow if the type is a scalar, multiplicity is not applicable here
                scalar_r = Relation.semijoin(db=mmdb, rname1=type_rv, rname2="Scalar")
                if scalar_r.body:
                    method_call_output_flow = Flow.populate_scalar_flow(activity_tr=tr_Call, scalar_type=type_name,
                                                                        anum=self.anum, domain=self.domain)
                else:  # Must be a table
                    method_call_output_flow = None  # placeholder
                    msg = "Unimplemented case: table output from called method"
                    _logger.exception(msg)
                    # TODO: Construct table name from method signature (need an example)
                pass

            Transaction.execute(db=mmdb, name=tr_Call)

            # Populate the output of the Method Call action (corresponds to the target Method's Synch Output)
            if not MethodCall.method_call_transaction_open:
                MethodCall.method_call_transaction_open = True
                Transaction.open(db=mmdb, name=MethodCall.tr_MethodCallOutput)

            Relvar.insert(db=mmdb, relvar="Method Call Output", tr=MethodCall.tr_MethodCallOutput, tuples=[
                Method_Call_Output_i(Method_call=self.action_id, Activity=self.anum, Domain=self.domain,
                                     Target_method=target_method_anum, Flow=method_call_output_flow.fid)
            ])

        return self.action_id, self.action_id, method_call_output_flow

