""" sexpr.py -- Walk through a scalar expression and populate elements """

# System
import logging
from typing import TYPE_CHECKING

# Model Integration
from scrall.parse.visitor import MATH_a, BOOL_a, INST_a, IN_a, N_a, Projection_a, Op_chain_a, INST_PROJ_a
from pyral.relation import Relation  # Keep for debugging

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.utility import print_mmdb  # Debugging
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.populate.actions.read_action import ReadAction
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Boundary_Actions
from xuml_populate.populate.actions.project_action import ProjectAction
from xuml_populate.populate.actions.type_action import TypeAction

_logger = logging.getLogger(__name__)


class ScalarExpr:
    """
    For reference, a scalar expression in the scrall grammar consists of terms

    term = (NOT SP*)? UNARY_MINUS? (scalar / "(" SP* sexpr SP* ")")
    scalar = value / QTY? scalar_chain
    scalar_chain = (ITS op_chain) / ((scalar_source / instance_set projection?) op_chain?)
    scalar_source = type_selector / input_param
    op_chain = ('.' (scalar_op / name))*
    scalar_op = name supplied_params

    So we need to walk through the parse tree through the nested operations, possibly
    building instance sets.
    """
    def __init__(self, expr: INST_PROJ_a | BOOL_a | N_a | IN_a | Op_chain_a, input_instance_flow: Flow_ap | None, activity: 'Activity'):
        """

        Args:
            expr: A parsed scalar expression
            input_instance_flow:
            activity:
        """
        self.expr = expr
        self.activity = activity
        self.input_instance_flow = input_instance_flow
        self.anum = activity.anum
        self.domain = activity.domain

        self.action_outputs = {}  # ID's of all Action output Data Flows
        self.action_inputs = {}  # ID's of all Action input Data Flows
        self.text = None  # A text representation of the expression
        self.component_flow = None
        self.output_tflow_id = None

    def process(self) -> tuple[Boundary_Actions, list[Flow_ap]]:
        """
        Walks through a scalar expression to obtain a tuple flow with one or more attributes. Each attribute value
        will be assigned. The order in which attributes are specified in the action language is returned along with
        the tuple flow.

        Returns:
            The output tuple flow and the attribute names as ordered in the scalar expression
        """
        # Obtain one or more scalar flows from the scalar expression that can flow values into an assigment on the lhs
        expr_sflows = self.walk(sexpr=self.expr, input_flow=self.input_instance_flow)

        all_ins = {v for s in self.action_inputs.values() for v in s}
        all_outs = {v for s in self.action_outputs.values() for v in s}
        if all_ins != all_outs:
            init_aids = {a for a in self.action_inputs.keys() if not self.action_inputs[a].intersection(all_outs)}
            final_aids = {a for a in self.action_outputs.keys() if not self.action_outputs[a].intersection(all_ins)}
        else:
            init_aids = {a for a in self.action_inputs.keys()}
            final_aids = {a for a in self.action_outputs.keys()}

        return Boundary_Actions(ain=init_aids, aout=final_aids), expr_sflows

    def resolve_iset(self, iset: INST_a, op_chain: Op_chain_a = None, projection: Projection_a = None) -> list[Flow_ap]:
        pass

    def walk(self, sexpr: str | INST_PROJ_a | MATH_a | BOOL_a | N_a | IN_a, input_flow: Flow_ap) -> list[Flow_ap]:
        """

        :param sexpr:  Parsed scalar expression
        :param input_flow:
        :return:  Output scalar flow
        """
        self.component_flow = input_flow
        match type(sexpr).__name__:
            case 'str':  # TRUE or FALSE string
                # we are assigining either true or false to the lhs, component flow will be scalar
                svalue_output = Flow.populate_scalar_flow(scalar_type="Boolean", anum=self.anum, domain=self.domain,
                                                          value=sexpr, label=None)
                return [svalue_output]
            case 'INST_PROJ_a':
                action_input = self.component_flow
                match type(sexpr.iset).__name__:
                    case 'N_a':
                        # There are no other iset components and since we project, this can't be a type name
                        # So there are only two possibilities and in case of a shadowing conflict, we must proceed
                        # in the order of conflict resolution precedence.
                        # 1. Check for an attribute name on the component flow class
                        # 2. Check for a scalar flow with this name
                        # Just in case there's another possibility, leave a placeholder for anything else

                        # Attribute check
                        R = f"Name:<{sexpr.iset.name}>, Class:<{self.component_flow.tname}>, Domain:<{self.domain}>"
                        attribute_r = Relation.restrict(db=mmdb, relation="Attribute", restriction=R)
                        if attribute_r.body:
                            # Create a read action to obtain the value
                            ra = ReadAction(input_single_instance_flow=self.component_flow, attrs=(sexpr.iset.name,),
                                            anum=self.anum, domain=self.domain)
                            aid, sflows = ra.populate()
                            return sflows

                        # Scalar flow check
                        sflows = Flow.find_labeled_scalar_flow(name=sexpr.iset.name, anum=self.anum,
                                                               domain=self.domain)
                        input_sflow = sflows[0] if sflows else None
                        # TODO: Check for case where multiple flows are returned

                        if input_sflow:
                            if sexpr.projection:
                                # This has to be a type operation and potentially a chain of multiple
                                first_action = True
                                component_flow = input_sflow
                                for a in sexpr.projection.attrs:
                                    ta = TypeAction(op_name=a.name, anum=self.anum, domain=self.domain,
                                                    input_flow=component_flow)
                                    ain, aout, component_flow = ta.populate()
                                    if first_action:
                                        self.action_inputs[ain] = {component_flow.fid}
                                        first_action = False
                                self.action_outputs[aout] = {component_flow.fid}
                                # If the parameter flow
                                return [component_flow]
                            else:
                                return [input_sflow]

                        # Instance flow check
                        input_iflows = Flow.find_labeled_ns_flow(name=sexpr.iset.name, anum=self.anum,
                                                                domain=self.domain)
                        if len(input_iflows) == 1:
                            input_iflow = input_iflows[0]
                        elif not input_iflows:
                            pass
                        else:
                            # TODO: Check case where multiple are returned
                            pass
                        if input_iflow:
                            # Verify that we are projecting on a single attribute
                            if not sexpr.projection:
                                msg = f"Instance flow in scalar expr has no projection"
                                _logger.error(msg)
                                raise ActionException(msg)
                            if not sexpr.projection.attrs:
                                msg = f"Instance flow in scalar expr does not project on any attribute names"
                                _logger.error(msg)
                                raise ActionException(msg)
                            if len(sexpr.projection.attrs) > 1:
                                msg = f"Instance flow in scalar expr projects on multiple attributes"
                                _logger.error(msg)
                                raise ActionException(msg)
                            attr_name = sexpr.projection.attrs[0].name

                            # Create a read action to obtain the value
                            ra = ReadAction(input_single_instance_flow=input_iflow, attrs=(attr_name,),
                                            anum=self.anum, domain=self.domain)
                            aid, sflows = ra.populate()
                            self.action_inputs[aid] = {self.component_flow.fid}
                            self.action_outputs[aid] = {s.fid for s in sflows}
                            return sflows

                        # No other recognized cases
                        msg = (f"Unknown scalar expression input for name: {sexpr.set.name} in "
                               f"{self.activity.activity_path}")
                        _logger.error(msg)
                        ActionException(msg)

                    case 'INST_a':
                        iset = InstanceSet(input_instance_flow=action_input, iset_components=sexpr.iset.components,
                                           activity=self.activity)
                        initial_aid, final_aid, self.component_flow = iset.process()
                        # Add the output flow generated by the instance set expression to the set of ouput flows
                        if initial_aid:
                            # For an InstanceSet with a single labled flow component, no action is created
                            # So don't process action inputs and outputs unless there is an initial_aid
                            self.action_inputs[initial_aid] = {action_input.fid}
                            if final_aid:
                                self.action_outputs[final_aid] = {self.component_flow.fid}
                        action_input = self.component_flow
                        project_attrs = tuple([a.name for a in sexpr.projection.attrs])
                        ra = ReadAction(input_single_instance_flow=action_input, attrs=project_attrs,
                                        anum=self.anum, domain=self.domain)
                        aid, sflows = ra.populate()
                        self.action_inputs[aid] = {action_input.fid}
                        self.action_outputs[aid] = {s.fid for s in sflows}
                        return sflows
            case 'N_a' | 'IN_a':
                # So there are only two possibilities and in case of a shadowing conflict, we must proceed
                # in the order of conflict resolution precedence.
                # 1. Check for an attribute name on the component flow class
                # 2. Check for a scalar flow with this name
                # Just in case there's a nother possibility, leave a placeholder for anything else
                if self.component_flow:
                    # Check for attribute only if there is an available component flow
                    # (which we won't have if this is an assigner activity, for example)
                    R = f"Name:<{sexpr.name}>, Class:<{self.component_flow.tname}>, Domain:<{self.domain}>"
                    attribute_r = Relation.restrict(db=mmdb, relation="Attribute", restriction=R)
                    if attribute_r.body:
                        # Create a read action to obtain the value
                        ra = ReadAction(input_single_instance_flow=self.component_flow, attrs=(sexpr.name,),
                                        anum=self.anum, domain=self.domain)
                        aid, sflows = ra.populate()
                        self.action_inputs[aid] = {self.component_flow.fid}
                        self.action_outputs[aid] = {s.fid for s in sflows}
                        return sflows
                # Not an attribute flow, look for a labeled scalar flow
                sflows = Flow.find_labeled_scalar_flow(name=sexpr.name, anum=self.anum, domain=self.domain)
                if not sflows:
                    msg = f"Name N_a in scalar expr must be an attribute or a labeled scalar flow"
                    _logger.error(msg)
                    raise ActionException(msg)
                return sflows

            case 'BOOL_a':
                pass
            case 'MATH_a':
                action_input = self.component_flow
                operand_flows = []
                op_name = sexpr.op
                for o in sexpr.operands:
                    match type(o).__name__:
                        case 'INST_PROJ_a':
                            iset = InstanceSet(input_instance_flow=action_input, iset_components=o.iset.components,
                                               activity=self.activity)
                            self.component_flow = iset.process()

                            if o.iset.select:
                                pass
                            if o.projection:
                                tflow = ProjectAction.populate(projection=o.projection,
                                                               input_nsflow=action_input,
                                                               activity=self.activity)
                                pass
                            pass
                        case _:
                            pass

                    operand_flows.append(self.walk(sexpr=o, input_flow=self.component_flow))
                pass
            case 'Op_chain_a':
                pass
            case _:
                _logger.error(
                    f"Expected .... but received {type(sexpr).__name__} during sexpr walk")
                raise ScalarOperationOrExpressionExpected
        # Process optional header, selection, and projection actions for the TEXPR
        return self.component_flow
