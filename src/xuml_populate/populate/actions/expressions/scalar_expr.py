""" sexpr.py -- Walk through a scalar expression and populate elements """

# System
import logging
from typing import TYPE_CHECKING, Optional

# Model Integration
from scrall.parse.visitor import MATH_a, BOOL_a, INST_a, IN_a, N_a, Projection_a, Op_chain_a, INST_PROJ_a
from pyral.relation import Relation  # Keep for debugging

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.populate.actions.read_action import ReadAction
from xuml_populate.populate.actions.extract_action import ExtractAction
from xuml_populate.populate.actions.expressions.op_chain import OpChain
from xuml_populate.populate.actions.type_selector import TypeSelector
from xuml_populate.populate.actions.computation_action import ComputationAction
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Boundary_Actions
from xuml_populate.populate.actions.project_action import ProjectAction
from xuml_populate.populate.actions.type_action import TypeAction
from xuml_populate.populate.actions.cardinality import CardinalityAction

if __debug__:
    from xuml_populate.utility import print_mmdb  # Debugging

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
    def __init__(self, expr: INST_PROJ_a | BOOL_a | N_a | IN_a | Op_chain_a, input_instance_flow: Flow_ap | None,
                 activity: 'Activity', cast_type: Optional[str] = None, bpart: bool = False):
        """
        Gather data required to process a scalar expression

        Args:
            expr: A parsed scalar expression
            input_instance_flow: The executing instance, if any
            activity: The enclosing activity object
        """
        self.cast_type = cast_type
        self.expr = expr
        self.bpart = bpart
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

    def resolve_name(self, name: str) -> Flow_ap:
        """
        Args:
            name:

        Returns:

        """
        # There are no other iset components and since we project, this can't be a type name
        # So there are only two possibilities and in case of a shadowing conflict, we must proceed
        # in the order of conflict resolution precedence.
        # 1. Check for an attribute name on the component flow class
        # 2. Check for a scalar flow with this name
        # Just in case there's another possibility, leave a placeholder for anything else

        # Attribute check
        R = f"Name:<{name}>, Class:<{self.component_flow.tname}>, Domain:<{self.domain}>"
        attribute_r = Relation.restrict(db=mmdb, relation="Attribute", restriction=R)
        if attribute_r.body:
            # Create a read action to obtain the value
            ra = ReadAction(input_single_instance_flow=self.component_flow, attrs=(name,),
                            anum=self.anum, domain=self.domain)
            aid, sflows = ra.populate()
            return sflows[0]

        # Scalar flow check
        sflows = Flow.find_labeled_scalar_flow(name=name, anum=self.anum,
                                               domain=self.domain)
        input_sflow = sflows[0] if sflows else None
        return input_sflow

    def walk(self, sexpr: str | INST_PROJ_a | MATH_a | BOOL_a | N_a | IN_a, input_flow: Flow_ap) -> list[Flow_ap]:
        """
        Args
            sexpr:  Parsed scalar expression
            input_flow:

        Returns
            List of output scalar flows
        """
        self.component_flow = input_flow
        sexpr_type = type(sexpr).__name__
        match sexpr_type:
            case 'str':  # TRUE or FALSE string
                # we are assigining either true or false to the lhs, component flow will be scalar
                svalue_output = Flow.populate_scalar_flow(scalar_type="Boolean", anum=self.anum, domain=self.domain,
                                                          value=sexpr, label=None)
                return [svalue_output]
            case 'INST_PROJ_a':
                action_input = self.component_flow
                iset_type = type(sexpr.iset).__name__
                match iset_type:
                    case 'N_a':
                        # There are no other iset components and since we project, this can't be a type name
                        # So there are only two possibilities and in case of a shadowing conflict, we must proceed
                        # in the order of conflict resolution precedence.
                        # 1. Check for an attribute name on the component flow class
                        # 2. Check for a scalar flow with this name
                        # Just in case there's another possibility, leave a placeholder for anything else

                        # Attribute check
                        read_sflows = None
                        R = f"Name:<{sexpr.iset.name}>, Class:<{self.component_flow.tname}>, Domain:<{self.domain}>"
                        attribute_r = Relation.restrict(db=mmdb, relation="Attribute", restriction=R)
                        if attribute_r.body:
                            # Create a read action to obtain the value
                            ra = ReadAction(input_single_instance_flow=self.component_flow, attrs=(sexpr.iset.name,),
                                            anum=self.anum, domain=self.domain)
                            aid, read_sflows = ra.populate()
                            self.action_inputs[aid] = {f.fid for f in read_sflows}
                            if not sexpr.projection and not sexpr.op_chain:
                                return read_sflows

                        # Scalar flow check
                        if read_sflows and len(read_sflows) == 1:
                            input_sflow = read_sflows[0]
                        else:
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
                                    # self.action_inputs[ain] = {input_sflow.fid}
                                    if first_action:
                                        # Now the Component flow has been updated to the output of the Type Action
                                        first_action = False
                                    self.action_outputs[aout] = {component_flow.fid}
                                # If the parameter flow
                                return [component_flow]
                            else:
                                return [input_sflow]

                        # Instance flow check
                        input_iflows = Flow.find_labeled_ns_flow(name=sexpr.iset.name, anum=self.anum,
                                                                 domain=self.domain)
                        input_iflow = input_iflows[0] if len(input_iflows) == 1 else None

                        if input_iflow:
                            if sexpr.qty:
                                # We aren't projecting, just returning the cardinality of the flow
                                ca = CardinalityAction(anum=self.anum, domain=self.domain, ns_flow=input_iflow)
                                caid, sflow = ca.populate()
                                self.action_outputs[caid] = {sflow.fid}
                                return [sflow]
                                pass
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

                            # Extract a scalar flow via either read or extract operations dependient on the flow
                            # content (Instance or Relation).

                            # Relation?  Populate Extract Action
                            if input_iflow.content == Content.RELATION:
                                if len(sexpr.projection.attrs) != 1:
                                    # For attribute comparison, there can only be one extracted attribute
                                    raise ActionException
                                attr_to_extract = sexpr.projection.attrs[0].name
                                xa = ExtractAction(tuple_flow=input_iflow, attr=attr_to_extract, activity=self.activity)
                                xa_aid, xa_sflow = xa.populate()
                                sflows = [xa_sflow]  # Extract outputs only a single flow
                                self.action_inputs[xa_aid] = {input_iflow.fid}
                                self.action_outputs[xa_aid] = {s.fid for s in sflows}
                                # TODO: Might want to change extract to make it output multiple like read
                                # TODO: For now, let's just make it single flow list for consistency with read output
                            elif input_iflow.content == Content.INSTANCE:
                                # Create a read action to obtain the value
                                ra = ReadAction(input_single_instance_flow=input_iflow, attrs=(attr_name,),
                                                anum=self.anum, domain=self.domain)
                                aid, sflows = ra.populate()
                                self.action_inputs[aid] = {input_iflow.fid}
                                self.action_outputs[aid] = {s.fid for s in sflows}
                            else:
                                pass
                            return sflows

                        # No other recognized cases
                        msg = (f"Unknown scalar expression input for name: {sexpr.iset.name} in "
                               f"{self.activity.activity_path}")
                        _logger.error(msg)
                        ActionException(msg)

                    case 'INST_a':
                        iset = InstanceSet(input_instance_flow=action_input, iset_components=sexpr.iset.components,
                                           activity=self.activity)
                        initial_aid, final_aid, self.component_flow = iset.process()
                        # Add the output flow generated by the instance set expression to the set of output flows
                        if initial_aid:
                            # For an InstanceSet with a single labled flow component, no action is created
                            # So don't process action inputs and outputs unless there is an initial_aid
                            self.action_inputs[initial_aid] = {action_input.fid}
                            if final_aid:
                                self.action_outputs[final_aid] = {self.component_flow.fid}
                        action_input = self.component_flow

                        # Are we counting the instances?
                        if sexpr.qty:
                            ca = CardinalityAction(anum=self.anum, domain=self.domain, ns_flow=self.component_flow)
                            caid, self.component_flow = ca.populate()
                            if sexpr.projection:
                                # Projection outside of a select statement has no utility here
                                # When you are counting instances, no projected attribute values will be output
                                msg = f"Incompatible cardinality instance set projection at {self.activity.activity_path}"
                                _logger.error(msg)
                                raise ActionException(msg)
                            self.action_outputs[final_aid] = caid

                        if sexpr.projection:
                            project_attrs = tuple([a.name for a in sexpr.projection.attrs])

                            # We are either reading the attributes of an instance or a tuple
                            if action_input.content == Content.INSTANCE:
                                ra = ReadAction(input_single_instance_flow=action_input, attrs=project_attrs,
                                                anum=self.anum, domain=self.domain)
                                aid, sflows = ra.populate()
                            elif action_input.content == Content.RELATION:
                                # We can extract only one attribute per action
                                sflows = []
                                for attr in project_attrs:
                                    xa = ExtractAction(tuple_flow=action_input, attr=attr, activity=self.activity)
                                    aid, sflow = xa.populate()
                                    sflows.append(sflow)
                            else:
                                # Can't read attributes from a Scalar flow
                                msg = (f"Non Scalar flow reauired to read or extract attribute values, "
                                       f"but input flow is: {action_input} in {self.activity.activity_path}")
                                _logger.error(msg)
                                raise ActionException(msg)
                        else:
                            sflows = [self.component_flow]
                            aid = final_aid

                        self.action_inputs[aid] = {action_input.fid}
                        self.action_outputs[aid] = {s.fid for s in sflows}

                        component_sflow = sflows[0]
                        if sexpr.op_chain:
                            oc = OpChain(iflow=None, sflow=component_sflow, parse=sexpr.op_chain, activity=self.activity)
                            b, s = oc.process()
                            sflows = [s]
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
                    msg = (f"Name N_a [{sexpr.name}] in scalar expr must be an attribute or a labeled scalar flow "
                           f"at {self.activity.activity_path}")
                    _logger.error(msg)
                    raise ActionException(msg)
                return sflows

            case 'BOOL_a' | 'MATH_a':
                ca = ComputationAction(expr=sexpr, activity=self.activity, cast_type=self.cast_type, bpart=self.bpart)
                b, sflows = ca.populate()
                self.action_inputs = {aid: {} for aid in b.ain}
                self.action_outputs = {aid: {} for aid in b.aout}
                return sflows
            case 'Op_chain_a':
                pass
            case _:
                _logger.error(
                    f"Expected .... but received {type(sexpr).__name__} during sexpr walk")
                raise ScalarOperationOrExpressionExpected
        # Process optional header, selection, and projection actions for the TEXPR
        return self.component_flow
