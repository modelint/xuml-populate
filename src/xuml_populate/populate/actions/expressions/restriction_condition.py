"""
restrict_condition.py – Process a select phrase and populate a Restriction Condition
"""

import logging
from xuml_populate.config import mmdb
from xuml_populate.exceptions.action_exceptions import ActionException
from typing import Optional, Set, Dict, List
from xuml_populate.populate.attribute import Attribute
from xuml_populate.populate.actions.validation.parameter_validation import validate_param
from xuml_populate.populate.actions.table_attribute import TableAttribute
from xuml_populate.populate.actions.aparse_types import (Flow_ap, MaxMult, Content, ActivityAP, Attribute_Comparison,
                                                         Attribute_ap)
from xuml_populate.populate.actions.read_action import ReadAction
from xuml_populate.populate.actions.extract_action import ExtractAction
from xuml_populate.exceptions.action_exceptions import ComparingNonAttributeInSelection, NoInputInstanceFlow
from xuml_populate.populate.mmclass_nt import Restriction_Condition_i, Equivalence_Criterion_i, \
    Comparison_Criterion_i, Criterion_i, Table_Restriction_Condition_i
from xuml_populate.populate.flow import Flow
from pyral.relvar import Relvar
from pyral.relation import Relation
from scrall.parse.visitor import N_a, BOOL_a, Op_a, Criteria_Selection_a

_logger = logging.getLogger(__name__)

# Transactions
tr_Restrict_Cond = "Restrict Condition"


class RestrictCondition:
    """
     -> (str, List[Attribute_Comparison], Set[Flow_ap]):
    Create all relations for a Restrict Condition for either a Select or Restrict Action
        Break down criteria into a set of attribute comparisons and validate the components of a Select Action that
        must be populated into the metamodel.
         | These components are:
        * Restriction Criterian (Comparison or Ranking)
        * Scalar Flow inputs to any Comparison Criterion
        Sift through criteria to ensure that each terminal is either an attribute, input flow, or value.
        :param tr:  The select or restrict action transaction
        :param action_id:
        :param input_nsflow:
        :param activity_data:
        :param selection_parse:
        :return: Selection cardinality, attribute comparisons, and a set of scalar flows input for attribute comparison
    """
    def __init__(self, tr: str, action_id: str, input_nsflow: Flow_ap, selection_parse: Criteria_Selection_a,
                 activity_data: ActivityAP):
        """

        :param tr:
        :param action_id:
        :param input_nsflow:
        :param selection_parse:
        :param activity_data:
        """

        self.action_id = action_id
        self.anum = activity_data.anum
        self.domain = activity_data.domain
        self.activity_data = activity_data
        self.tr = tr
        self.comparison_criteria = []
        self.input_scalar_flows = set()
        self.input_nsflow = input_nsflow
        self.expression = ""
        self.criterion_ctr = 0

        criteria = selection_parse.criteria
        # Consider case where there is a single boolean value critieria such as:
        #   shaft aslevs( Stop requested )
        # The implication is that we are selecting on: Stop requested == true
        # So elaborate the parse elminating our shorthand
        self.cardinality = selection_parse.card
        if type(criteria).__name__ == 'N_a':
            self.expression = self.walk_criteria(operands=[criteria])
            pass
            # criteria = BOOL_a(op='==', operands=[criteria, N_a(name='true')])
            # Name only (no explicit operator or operand)
        else:
            self.expression = self.walk_criteria(operands=criteria.operands, operator=criteria.op)
            pass
        # Walk the parse tree and save all attributes, ops, values, and input scalar flows
        # Populate the Restriction Condition class
        Relvar.insert(db=mmdb, tr=tr, relvar='Restriction_Condition', tuples=[
            Restriction_Condition_i(Action=self.action_id, Activity=self.anum, Domain=self.domain,
                                    Expression=self.expression.strip(), Selection_cardinality=self.cardinality
                                    )
        ])
        # return cardinality, self.comparison_criteria, self.input_scalar_flows

    def walk_criteria(self, operands: List, operator: Optional[str] = None, attr: Optional[str] = None):
        """
        Recursively walk down the selection criteria parse tree validating attributes and input flows found in
        the leaf nodes. Also flatten the parse back into a language independent text representation for reference
        in the metamodel.

        :param operator:  A boolean, math or unary operator
        :param operands:  One or two operands (depending on the operator)
        :param attr:  If true, an attribute is in the process of being compared to an expression
        :return: Flattened selection expression as a string
        """
        attr_set = attr  # Has an attribute been set for this invocation?
        text = ""
        assert len(operands) <= 2
        for o in operands:
            match type(o).__name__:
                case 'IN_a':
                    # Verify that this input is defined on the enclosing Activity
                    validate_param(name=o.name, activity=self.activity_data)
                    if not attr_set:
                        # The Attribute has the same name as the Parameter
                        # We assume that attribute names are capitalized so the name doubling shorthand for
                        # params only works if this convention is followed.
                        Attribute.scalar(name=o.name.capitalize(), tname=self.input_nsflow.tname, domain=self.domain)
                        criterion_id = self.pop_xi_comparison_criterion(attr=o.name)
                    else:
                        # We know this is not an Attribute since it is a scalar flow label coming in as a Parameter
                        criterion_id = self.pop_comparison_criterion(attr=attr_set.name, op=operator, scalar_flow_label=o.name)
                    text += f" {criterion_id}"
                case 'N_a':
                    if not operator or operator in {'AND', 'OR'}:
                        if operator in {'AND', 'OR'}:
                            text += f" {operator}"
                        # This covers shorthand cases like:
                        #     ( Inservice ) -> Boolean equivalence: ( Inservice == True )
                        #     ( Held AND Blocked ) ->   same: ( Held == True AND Blocked == True )
                        # Short hand on the left and explicit equivalent longhand to the right,
                        # so the above cases leave the == True part implicit
                        # As well as name doubling shorthand:
                        #     ( Shaft ) -> Non-boolean comparison: ( Shaft == me.Shaft )
                        # The longhand form compares the value of the source instance flow attribute with the
                        # same named attribute in the xi instance. Our use of referential attributes in SM makes
                        # this sort of thing common.

                        # In all of these cases we must have an Attribute of a Class, but we verify that here
                        scalar = Attribute.scalar(name=o.name, tname=self.input_nsflow.tname, domain=self.domain)
                        # An exception is raised in the above if the Attribute is undefined

                        # Now we check the Scalar (Type) to determine whether we populate an Equivalence or
                        # Comparison Criterion
                        if scalar == 'Boolean':
                            # Populate a simple equivalence criterion
                            criterion_id = self.pop_boolean_equivalence_criterion(not_op=False, attr=o.name, value="true")
                        else:
                            # Populate a comparison
                            criterion_id = self.pop_xi_comparison_criterion(attr=o.name)
                        text += f" {criterion_id}"
                    elif not attr_set:
                        # We know that the operator is a comparison op (==, >=, etc) which means that
                        # the first operand is an Attribute and the second is a scalar expression
                        # TODO: ignore NOT operator for now
                        # And that since the attribute hasn't been set yet, this must be the left side of the
                        # comparison and, hence, the attribute
                        # We verify this:
                        scalar = Attribute.scalar(name=o.name, tname=self.input_nsflow.tname, domain=self.domain)
                        # The criterion is populated when the second operand is processed, so all we need to do
                        # now is to remember the Attribute name
                        attr_set = Attribute_ap(o.name, scalar)
                    else:
                        # The scalar expression on the right side of the comparison must be a scalar flow
                        # an enum, or a boolean value
                        if o.name.startswith('_'):
                            # This name is an enum value
                            # TODO: Validate the enum value as a member of the Attribute's Scalar
                            criterion_id = self.pop_equivalence_criterion(attr=attr_set.name, op=operator, value=o.name,
                                                          scalar=attr_set.scalar)
                        elif (n := o.name.lower()) in {'true', 'false'}:
                            # This name is a boolean value
                            criterion_id = self.pop_boolean_equivalence_criterion(not_op=False, attr=attr_set, value=n)
                        else:
                            # It must be the name of a scalar flow that should have been set with some value
                            criterion_id = self.pop_comparison_criterion(scalar_flow_label=o.name, attr=attr_set.name, op=operator)
                        text += f" {criterion_id}"

                case 'BOOL_a':
                    criterion_id = self.walk_criteria(operands=o.operands, operator=o.op, attr=attr_set)
                    text += f" {criterion_id}"
                case 'MATH_a':
                    criterion_id = self.walk_criteria(operands=o.operands, operator=o.op, attr=attr_set)
                    text += f" {criterion_id}"
                case 'UNARY_a':
                    pass # TODO: tbd
                case 'INST_PROJ_a':
                    match type(o.iset).__name__:
                        case 'N_a':
                            if o.projection:
                                # This must be a Non Scalar Flow
                                # If it is an Instance Flow, an attribute will be read with a Read Action
                                # Otherwise, a Tuple Flow will have a value extracted with an Extract Action

                                sflow = None  # This is the scalar flow result of the projection/extraction
                                ns_flow = Flow.find_labeled_ns_flow(name=o.iset.name, anum=self.anum, domain=self.domain)
                                if not ns_flow:
                                    raise ActionException
                                if ns_flow.content == Content.INSTANCE:
                                    # TODO: Fill out the read action case
                                    ReadAction.populate()
                                elif ns_flow.content == Content.RELATION:
                                    if len(o.projection.attrs) != 1:
                                        # For attribute comparison, there can only be one extracted attribute
                                        raise ActionException
                                    attr_to_extract = o.projection.attrs[0].name
                                    extract_action = ExtractAction(
                                        tuple_flow=ns_flow, attr=attr_to_extract, anum=self.anum,
                                        domain=self.domain, activity_data=self.activity_data
                                    )  # Select Action transaction is open
                                    sflow = extract_action.output_sflow
                                # Now populate a comparison criterion
                                criterion_id = self.pop_comparison_criterion(attr=o.projection.attrs[0].name, scalar_flow=sflow, op=operator)
                                text += f" {criterion_id}"
                            else:
                                # This must be a Scalar Flow
                                # TODO: check need for mmdb param
                                sflow = Flow.find_labeled_scalar_flow(name=o.iset.name, anum=self.anum,
                                                                      domain=self.domain)
                                if not sflow:
                                    raise ActionException
                            pass
                        case 'IN_a':
                            pass
                        case 'INST_a':
                            pass
                            # TODO: create what's needed when we hit this case (previously order expr)
                        case _:
                            raise ActionException
                    # TODO: Now process the projection
                    pass
                case _:
                    raise Exception
        return text

    def pop_xi_comparison_criterion(self, attr: str) -> int:
        """
        Let's say that we are performing a select/restrict on some Class and comparing the value of some
        attribute named X on that Class. If the executing instance (xi) also has an attribute named X,
        we can read that value and supply it in the comparison criterion.

        Here we populate a Read Action on the executing instance (xi) to read the value of the matching
        Attribute.

        :param attr: Name of some compared Attribute that matches an Attribute of the executing instance
        """
        read_iflow = Flow_ap(fid=self.activity_data.xiflow, tname=self.activity_data.cname, content=Content.INSTANCE,
                             max_mult=MaxMult.ONE)
        _, read_flows = ReadAction.populate(input_single_instance_flow=read_iflow,
                                            attrs=(attr,),
                                            anum=self.anum, domain=self.domain)
        assert len(read_flows) == 1
        # Since we are reading a single attribute, assume only one output flow
        return self.pop_comparison_criterion(attr=attr, op='==', scalar_flow=read_flows[0])

    def pop_comparison_criterion(self, attr: str, op: str, scalar_flow_label: Optional[str] = None,
                                 scalar_flow: Optional[Flow_ap] = None) -> int:
        """

        :param attr:
        :param op:
        :param scalar_flow_label:
        :param scalar_flow:
        :return: criterion id
        """
        if not scalar_flow:
            if not scalar_flow_label:
                raise ActionException
            sflow = Flow.find_labeled_scalar_flow(name=scalar_flow_label, anum=self.anum, domain=self.domain)
        else:
            sflow = scalar_flow
        self.input_scalar_flows.add(sflow)
        if not sflow:
            raise ActionException  # TODO: Make specific
        criterion_id = self.pop_criterion(attr)
        Relvar.insert(db=mmdb, tr=self.tr, relvar='Comparison_Criterion', tuples=[
            Comparison_Criterion_i(ID=criterion_id, Action=self.action_id, Activity=self.anum, Attribute=attr,
                                   Comparison=op, Value=sflow.fid, Domain=self.domain)
        ])
        self.comparison_criteria.append(Attribute_Comparison(attr, op))
        return criterion_id

    def pop_criterion(self, attr: str) -> int:
        """

        :param attr:
        :return: criterion id
        """
        self.criterion_ctr += 1
        criterion_id = self.criterion_ctr
        Relvar.insert(db=mmdb, tr=self.tr, relvar='Criterion', tuples=[
            Criterion_i(ID=criterion_id, Action=self.action_id, Activity=self.anum, Attribute=attr,
                        Non_scalar_type=self.input_nsflow.tname, Domain=self.domain)
        ])
        return criterion_id

    def pop_equivalence_criterion(self, attr: str, op: str, value: str, scalar: str) -> int:
        """
        Populates either a boolean or enum equivalence

        :param attr: Attribute name
        :param op: Either eq or ne (== !=)
        :param value: Enum value or true
        :param scalar: Scalar name
        """
        # Populate the Restriction Criterion superclass
        criterion_id = self.pop_criterion(attr=attr)
        # Populate the Equivalence Criterion
        Relvar.insert(db=mmdb, tr=self.tr, relvar='Equivalence_Criterion', tuples=[
            Equivalence_Criterion_i(ID=criterion_id, Action=self.action_id, Activity=self.anum,
                                    Attribute=attr, Domain=self.domain, Operation=op,
                                    Value=value, Scalar=scalar)
        ])
        return criterion_id

    def pop_boolean_equivalence_criterion(self, not_op: bool, attr: str, value: str) -> int:
        """
        An Equivalence Criterion is populated when a boolean value is compared
        against an Attribute typed Boolean

        :param not_op: True if attribute preceded by NOT operator in expression
        :param attr: Attribute name
        :param value:  Attribute is compared to either "true" / "false"
        :return: criterion id
        """
        return self.pop_equivalence_criterion(attr=attr, op="ne" if not_op else "eq", value=value, scalar="Boolean")

