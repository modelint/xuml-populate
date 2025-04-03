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
from xuml_populate.populate.actions.aparse_types import (Flow_ap, MaxMult, Content, Activity_ap, Attribute_Comparison,
                                                         Attribute_ap)
from xuml_populate.populate.actions.read_action import ReadAction
from xuml_populate.populate.actions.extract_action import ExtractAction
from xuml_populate.exceptions.action_exceptions import ComparingNonAttributeInSelection, NoInputInstanceFlow
from xuml_populate.populate.mmclass_nt import Restriction_Condition_i, Equivalence_Criterion_i, \
    Comparison_Criterion_i, Ranking_Criterion_i, Criterion_i, Table_Restriction_Condition_i
from xuml_populate.populate.flow import Flow
from pyral.relvar import Relvar
from pyral.relation import Relation
from scrall.parse.visitor import N_a, BOOL_a, Op_a, Selection_a

_logger = logging.getLogger(__name__)

# Transactions
tr_Restrict_Cond = "Restrict Condition"


class RestrictCondition:
    """
    Create all relations for a Restrict Condition for either a Select or Restrict Action
    """

    action_id = None
    input_nsflow = None
    anum = None
    domain = None  # in this domain
    activity_data = None
    tr = None  # Open Select or Restrict Action transaction

    expression = None
    comparison_criteria = None
    criterion_ctr = 0
    input_scalar_flows = None

    @classmethod
    def pop_xi_comparison_criterion(cls, attr: str):
        """
        Let's say that we are performing a select/restrict on some Class and comparing the value of some
        attribute named X on that Class. If the executing instance (xi) also has an attribute named X,
        we can read that value and supply it in the comparison criterion.

        Here we populate a Read Action on the executing instance (xi) to read the value of the matching
        Attribute.

        :param attr: Name of some compared Attribute that matches an Attribute of the executing instance
        """
        read_iflow = Flow_ap(fid=cls.activity_data.xiflow, tname=cls.activity_data.cname, content=Content.INSTANCE,
                             max_mult=MaxMult.ONE)
        _, read_flows = ReadAction.populate(input_single_instance_flow=read_iflow,
                                            attrs=(attr,),
                                            anum=cls.anum, domain=cls.domain)
        assert len(read_flows) == 1
        # Since we are reading a single attribute, assume only one output flow
        cls.pop_comparison_criterion(attr=attr, op='==', scalar_flow=read_flows[0])

    @classmethod
    def pop_comparison_criterion(cls, attr: str, op: str, scalar_flow_label: Optional[str] = None,
                                 scalar_flow: Optional[Flow_ap] = None):
        """

        :param attr:
        :param op:
        :param scalar_flow_label:
        :param scalar_flow:
        :return:
        """
        if not scalar_flow:
            if not scalar_flow_label:
                raise ActionException
            sflow = Flow.find_labeled_scalar_flow(name=scalar_flow_label, anum=cls.anum, domain=cls.domain)
        else:
            sflow = scalar_flow
        cls.input_scalar_flows.add(sflow)
        if not sflow:
            raise ActionException  # TODO: Make specific
        criterion_id = cls.pop_criterion(attr)
        Relvar.insert(mmdb, tr=cls.tr, relvar='Comparison_Criterion', tuples=[
            Comparison_Criterion_i(ID=criterion_id, Action=cls.action_id, Activity=cls.anum, Attribute=attr,
                                   Comparison=op, Value=sflow.fid, Domain=cls.domain)
        ])
        cls.comparison_criteria.append(Attribute_Comparison(attr, op))

    @classmethod
    def pop_ranking_criterion(cls, order: str, attr: str):
        """

        :param order:
        :param attr:
        :return:
        """
        criterion_id = cls.pop_criterion(attr)
        Relvar.insert(mmdb, tr=cls.tr, relvar='Ranking_Criterion', tuples=[
            Ranking_Criterion_i(ID=criterion_id, Action=cls.action_id, Activity=cls.anum, Attribute=attr,
                                Order=order, Domain=cls.domain)
        ])

    @classmethod
    def pop_criterion(cls, attr: str) -> int:
        """

        :param attr:
        :return:
        """
        cls.criterion_ctr += 1
        criterion_id = cls.criterion_ctr
        Relvar.insert(mmdb, tr=cls.tr, relvar='Criterion', tuples=[
            Criterion_i(ID=criterion_id, Action=cls.action_id, Activity=cls.anum, Attribute=attr,
                        Non_scalar_type=cls.input_nsflow.tname, Domain=cls.domain)
        ])
        return criterion_id

    @classmethod
    def pop_equivalence_criterion(cls, attr: str, op: str, value: str, scalar: str):
        """
        Populates either a boolean or enum equivalence

        :param attr: Attribute name
        :param op: Either eq or ne (== !=)
        :param value: Enum value or true
        :param scalar: Scalar name
        """
        # Populate the Restriction Criterion superclass
        criterion_id = cls.pop_criterion(attr=attr)
        # Populate the Equivalence Criterion
        Relvar.insert(mmdb, tr=cls.tr, relvar='Equivalence_Criterion', tuples=[
            Equivalence_Criterion_i(ID=criterion_id, Action=cls.action_id, Activity=cls.anum,
                                    Attribute=attr, Domain=cls.domain, Operation=op,
                                    Value=value, Scalar=scalar)
        ])

    @classmethod
    def pop_boolean_equivalence_criterion(cls, not_op: bool, attr: str, value: str):
        """
        An Equivalence Criterion is populated when a boolean value is compared
        against an Attribute typed Boolean

        :param not_op: True if attribute preceded by NOT operator in expression
        :param attr: Attribute name
        :param value:  Attribute is compared to either "true" / "false"
        """
        cls.pop_equivalence_criterion(attr=attr, op="ne" if not_op else "eq", value=value, scalar="Boolean")

    @classmethod
    def walk_criteria(cls, operands: List, operator: Optional[str] = None, attr: Optional[str] = None) -> str:
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
        text = f" {'' if not operator else operator} "  # Flatten operator into temporary string
        assert len(operands) <= 2
        for o in operands:
            match type(o).__name__:
                case 'IN_a':
                    # Verify that this input is defined on the enclosing Activity
                    validate_param(name=o.name, activity=cls.activity_data)
                    if not attr_set:
                        # The Attribute has the same name as the Parameter
                        # We assume that attribute names are capitalized so the name doubling shorthand for
                        # params only works if this convention is followed.
                        Attribute.scalar(name=o.name.capitalize(), cname=cls.input_nsflow.tname, domain=cls.domain)
                        cls.pop_xi_comparison_criterion(attr=o.name)
                    else:
                        # We know this is not an Attribute since it is a scalar flow label coming in as a Parameter
                        cls.pop_comparison_criterion(attr=attr_set.name, op=operator, scalar_flow_label=o.name)
                    text += f" {o.name}"
                case 'N_a':
                    if not operator or operator in {'AND', 'OR'}:
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
                        scalar = Attribute.scalar(name=o.name, cname=cls.input_nsflow.tname, domain=cls.domain)
                        # An exception is raised in the above if the Attribute is undefined

                        # Now we check the Scalar (Type) to determine whether we populate an Equivalence or
                        # Comparison Criterion
                        if scalar == 'Boolean':
                            # Populate a simple equivalence criterion
                            cls.pop_boolean_equivalence_criterion(not_op=False, attr=o.name, value="true")
                        else:
                            # Populate a comparison
                            cls.pop_xi_comparison_criterion(attr=o.name)
                    elif not attr_set:
                        # We know that the operator is a comparison op (==, >=, etc) which means that
                        # the first operand is an Attribute and the second is a scalar expression
                        # TODO: ignore NOT operator for now
                        # And that since the attribute hasn't been set yet, this must be the left side of the
                        # comparison and, hence, the attribute
                        # We verify this:
                        scalar = Attribute.scalar(name=o.name, cname=cls.input_nsflow.tname, domain=cls.domain)
                        # The criterion is populated when the second operand is processed, so all we need to do
                        # now is to remember the Attribute name
                        attr_set = Attribute_ap(o.name, scalar)
                    else:
                        # The scalar expression on the right side of the comparison must be a scalar flow
                        # an enum, or a boolean value
                        if o.name.startswith('_'):
                            # This name is an enum value
                            # TODO: Validate the enum value as a member of the Attribute's Scalar
                            cls.pop_equivalence_criterion(attr=attr_set.name, op=operator, value=o.name,
                                                          scalar=attr_set.scalar)
                        elif (n := o.name.lower()) in {'true', 'false'}:
                            # This name is a boolean value
                            cls.pop_boolean_equivalence_criterion(not_op=False, attr=attr_set, value=n)
                        else:
                            # It must be the name of a scalar flow that should have been set with some value
                            cls.pop_comparison_criterion(scalar_flow_label=o.name, attr=attr_set, op=operator)

                        # Update the text expression
                        if not attr_set:
                            text = f"{o.name} {text}"
                        else:
                            text = f"{text} {o.name}"
                case 'BOOL_a':
                    text += cls.walk_criteria(operands=o.operands, operator=o.op, attr=attr_set)
                case 'MATH_a':
                    text += cls.walk_criteria(operands=o.operands, operator=o.op, attr=attr_set)
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
                                ns_flow = Flow.find_labeled_ns_flow(name=o.iset.name, anum=cls.anum, domain=cls.domain)
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
                                    sflow = ExtractAction.populate(tuple_flow=ns_flow,
                                                                   attr=attr_to_extract, anum=cls.anum,
                                                                   domain=cls.domain, activity_data=cls.activity_data,
                                                                   )  # Select Action transaction is open
                                # Now populate a comparison criterion
                                cls.pop_comparison_criterion(attr=o.projection.attrs[0].name, scalar_flow=sflow, op=operator)
                                text += "<projection>"
                            else:
                                # This must be a Scalar Flow
                                # TODO: check need for mmdb param
                                sflow = Flow.find_labeled_scalar_flow(name=o.iset.name, anum=cls.anum,
                                                                      domain=cls.domain)
                                if not sflow:
                                    raise ActionException
                            pass
                        case 'IN_a':
                            pass
                        case 'INST_a':
                            i = o.iset.components
                            if len(i) == 1:
                                match type(i[0]).__name__:
                                    case 'Order_name_a':
                                        # This is a Ranking Criterion
                                        attr_name = i[0].name.name
                                        order = i[0].order
                                        cls.pop_ranking_criterion(order=order, attr=attr_name)
                                        attr_set = attr_name
                                        text = f"{order.upper()}({attr_name}) " + text
                                        pass
                                    case _:
                                        raise ActionException
                            else:
                                raise ActionException
                        case _:
                            raise ActionException
                    # TODO: Now process the projection
                    pass
                case _:
                    raise Exception
        return text

    @classmethod
    def process(cls, tr: str, action_id: str, input_nsflow: Flow_ap, selection_parse: Selection_a,
                activity_data: Activity_ap) -> (str, List[Attribute_Comparison], Set[Flow_ap]):
        """
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
        cls.action_id = action_id
        cls.anum = activity_data.anum
        cls.domain = activity_data.domain
        cls.activity_data = activity_data
        cls.tr = tr
        cls.comparison_criteria = []
        cls.input_scalar_flows = set()

        cls.input_nsflow = input_nsflow
        criteria = selection_parse.criteria
        # Consider case where there is a single boolean value critieria such as:
        #   shaft aslevs( Stop requested )
        # The implication is that we are selecting on: Stop requested == true
        # So elaborate the parse elminating our shorhand
        cardinality = 'ONE' if selection_parse.card == '1' else 'ALL'
        if type(criteria).__name__ == 'N_a':
            cls.expression = cls.walk_criteria(operands=[criteria])
            # criteria = BOOL_a(op='==', operands=[criteria, N_a(name='true')])
            # Name only (no explicit operator or operand)
        else:
            cls.expression = cls.walk_criteria(operands=criteria.operands, operator=criteria.op)
        # Walk the parse tree and save all attributes, ops, values, and input scalar flows
        # Populate the Restriction Condition class
        Relvar.insert(mmdb, tr=tr, relvar='Restriction_Condition', tuples=[
            Restriction_Condition_i(Action=cls.action_id, Activity=cls.anum, Domain=cls.domain,
                                    Expression=cls.expression, Selection_cardinality=cardinality
                                    )
        ])
        return cardinality, cls.comparison_criteria, cls.input_scalar_flows
