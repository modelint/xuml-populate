"""
restrict_condition.py – Process a select phrase and populate a Restriction Condition
"""

import logging
from xuml_populate.config import mmdb
from xuml_populate.exceptions.action_exceptions import ActionException
from typing import Optional, Set, Dict, List
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap, Attribute_Comparison
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
    input_scalar_flows = set()

    @classmethod
    def pop_comparison_criterion(cls, attr: str, op: str, scalar_flow_label: Optional[str] = None,
                                 scalar_flow: Optional[Flow_ap] = None):
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

    @classmethod
    def pop_ranking_criterion(cls, order: str, attr: str, op: str):
        # Validate the attribute and add to comparison criteria
        cls.process_attr(name=attr, op=op)
        criterion_id = cls.pop_criterion(attr)
        Relvar.insert(mmdb, tr=cls.tr, relvar='Ranking_Criterion', tuples=[
            Ranking_Criterion_i(ID=criterion_id, Action=cls.action_id, Activity=cls.anum, Attribute=attr,
                                Order=order, Domain=cls.domain)
        ])

    @classmethod
    def pop_criterion(cls, attr: str) -> int:
        cls.criterion_ctr += 1
        criterion_id = cls.criterion_ctr
        Relvar.insert(mmdb, tr=cls.tr, relvar='Criterion', tuples=[
            Criterion_i(ID=criterion_id, Action=cls.action_id, Activity=cls.anum, Attribute=attr,
                        Non_scalar_type=cls.input_nsflow.tname, Domain=cls.domain)
        ])
        return criterion_id

    @classmethod
    def process_bool_value(cls, attr: str, op: str, setting: bool):
        """
        An Equivalence Criterion is populated when a boolean value is compared
        against an Attribute typed Boolean

        :param scalar_flow_label:
        :param attr: THe name of the class attribute typed boolean
        :param op: The comparision operation as ==
        :param setting:
        :return:
        """
        # Populate the Restriction Criterion superclass
        criterion_id = cls.pop_criterion(attr=attr)
        # Populate the Equivalence Criterion
        Relvar.insert(mmdb, tr=cls.tr, relvar='Equivalence_Criterion', tuples=[
            Equivalence_Criterion_i(ID=criterion_id, Action=cls.action_id, Activity=cls.anum,
                                    Attribute=attr, Domain=cls.domain, Operation="true" if op == "==" else "false",
                                    Value="true" if setting else "false", Scalar="Boolean")
        ])

    @classmethod
    def process_enum_value(cls, attr: str, op: str, enum: str):
        pass

    @classmethod
    def process_attr(cls, name: str, op: str):
        """
        Validate that attribute is a member of the input flow class or table

        :param op:
        :param name:
        :return:
        """
        if cls.input_nsflow.content == Content.INSTANCE:
            R = f"Name:<{name}>, Class:<{cls.input_nsflow.tname}>, Domain:<{cls.domain}>"
            result = Relation.restrict(mmdb, relation='Attribute', restriction=R)
            if not result.body:
                raise ComparingNonAttributeInSelection(f"select action restriction on class"
                                                       f"[{cls.input_nsflow.tname}] is "
                                                       f"comparing on name [{name}] that is not an attribute of that class")
            cls.comparison_criteria.append(Attribute_Comparison(attr=name, op=op))
        elif cls.input_nsflow.content == Content.RELATION:
            R = f"Name:<{name}>, Table:<{cls.input_nsflow.tname}>, Domain:<{cls.domain}>"
            result = Relation.restrict(mmdb, relation='Table_Attribute', restriction=R)
            if not result.body:
                raise ComparingNonAttributeInSelection(f"select action restriction on class"
                                                       f"[{cls.input_nsflow.tname}] is "
                                                       f"comparing on name [{name}] that is not an attribute of that class")
            cls.comparison_criteria.append({'attr': name, 'op': op})

    @classmethod
    def walk_criteria(cls, operator, operands, attr: Optional[str] = None) -> str:
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
        text = f" {operator} "  # Flatten operator into temporary string
        for o in operands:
            match type(o).__name__:
                case 'IN_a':
                    pass
                    # cls.process_flow(name=o, op=operator, input_param=True)
                    # text += f" {o.name}"
                case 'N_a':
                    if not attr_set:
                        # It must be the name of some attribute of the class selected upon
                        cls.process_attr(name=o.name, op=operator)
                        text = f"{o.name} {text}"
                        attr_set = o.name
                        # Otherwise, not an attribute, process as a constant value or scalar input flow
                    else:
                        text += f" {o.name}"
                        if o.name.startswith('_'):
                            # It's an enum value
                            cls.process_enum_value(attr=attr_set, op=operator, enum=o.name)
                        elif (n := o.name.lower()) in {'true', 'false'}:
                            # It's a boolean value
                            cls.process_bool_value(attr=attr_set, op=operator, setting=(n == 'true'))
                        else:
                            # It must be the name of a scalar flow that should have been set with some value
                            cls.pop_comparison_criterion(scalar_flow_label=o.name, attr=attr_set, op=operator)
                            pass
                case 'BOOL_a':
                    text += cls.walk_criteria(o.op, o.operands, attr_set)
                case 'MATH_a':
                    text += cls.walk_criteria(o.op, o.operands, attr_set)
                case 'UNARY_a':
                    print()
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
                                cls.pop_comparison_criterion(attr=o.projection.attrs[0], scalar_flow=sflow, op=operator)
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
                                        cls.pop_ranking_criterion(order=order, attr=attr_name, op=operator)
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

        cls.input_nsflow = input_nsflow
        criteria = selection_parse.criteria
        # Consider case where there is a single boolean value critieria such as:
        #   shaft aslevs( Stop requested )
        # The implication is that we are selecting on: Stop requested == true
        # So elaborate the parse elminating our shorhand
        cardinality = 'ONE' if selection_parse.card == '1' else 'ALL'
        if type(criteria).__name__ == 'N_a':
            # Name only (no explicit operator or operand)
            criteria = BOOL_a(op='==', operands=[criteria, N_a(name='true')])
        # Walk the parse tree and save all attributes, ops, values, and input scalar flows
        cls.expression = cls.walk_criteria(criteria.op, criteria.operands)
        # Populate the Restriction Condition class
        Relvar.insert(mmdb, tr=tr, relvar='Restriction_Condition', tuples=[
            Restriction_Condition_i(Action=cls.action_id, Activity=cls.anum, Domain=cls.domain,
                                    Expression=cls.expression, Selection_cardinality=cardinality
                                    )
        ])
        return cardinality, cls.comparison_criteria, cls.input_scalar_flows
