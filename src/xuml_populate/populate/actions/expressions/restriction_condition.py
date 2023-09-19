"""
restrict_condition.py – Process a select phrase and populate a Restriction Condition
"""

import logging
from typing import TYPE_CHECKING, Optional
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap
from xuml_populate.exceptions.action_exceptions import ComparingNonAttributeInSelection, NoInputInstanceFlow
from xuml_populate.populate.mmclass_nt import Restriction_Condition_i, Equivalence_Criterion_i, \
    Comparison_Criterion_i, Ranking_Criterion_i, Criterion_i
from pyral.relvar import Relvar
from pyral.relation import Relation
from scrall.parse.visitor import N_a, BOOL_a, Op_a, Selection_a

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class RestrictCondition:
    """
    Create all relations for a Restrict Condition for either a Select or Restrict Action
    """

    mmdb = None  # The database
    action_id = None
    input_nsflow = None
    anum = None
    domain = None  # in this domain

    expression = None
    comparison_criteria = []
    equivalence_criteria = []
    restriction_text = ""
    criterion_ctr = 0

    @classmethod
    def pop_restriction_criterion(cls, attr: str) -> int:
        cls.criterion_ctr += 1
        criterion_id = cls.criterion_ctr
        Relvar.insert(relvar='Criterion', tuples=[
            Criterion_i(ID=criterion_id, Action=cls.action_id, Activity=cls.anum, Attribute=attr,
                        Non_scalar_type=cls.input_nsflow.tname, Domain=cls.domain)
        ])
        return criterion_id

    @classmethod
    def process_bool_value(cls, attr: str, op: str, setting: bool):
        """
        An Equivalence Criterion is populated when a boolean value is compared
        against an Attribute typed Boolean

        :param attr: THe name of the class attribute typed boolean
        :param op: The comparision operation as ==
        :param setting:
        :return:
        """
        # Populate the Restriction Criterion superclass
        criterion_id = cls.pop_restriction_criterion(attr=attr)
        # Populate the Equivalence Criterion
        Relvar.insert(relvar='Equivalence_Criterion', tuples=[
            Equivalence_Criterion_i(ID=criterion_id, Action=cls.action_id, Activity=cls.anum,
                                    Attribute=attr, Domain=cls.domain, Operation="true" if op == "==" else "false",
                                    Value="true" if setting else "false", Scalar="Boolean")
        ])

    @classmethod
    def process_enum_value(cls, attr: str, op: str, enum: str):
        pass

    @classmethod
    def process_flow(cls, name: str, op: str, input_param: bool = False):
        print(f"Populating [{name}] as flow")

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
            result = Relation.restrict(cls.mmdb, relation='Attribute', restriction=R)
            if not result.body:
                raise ComparingNonAttributeInSelection(f"select action restriction on class"
                                                       f"[{cls.input_nsflow.tname}] is "
                                                       f"comparing on name [{name}] that is not an attribute of that class")
            cls.comparison_criteria.append({'attr': name, 'op': op})
        elif cls.input_nsflow.content == Content.TABLE:
            R = f"Name:<{name}>, Table:<{cls.input_nsflow.tname}>, Domain:<{cls.domain}>"
            result = Relation.restrict(cls.mmdb, relation='Table_Attribute', restriction=R)
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
                    cls.process_flow(name=o, op=operator, input_param=True)
                    text += f" {o.name}"
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
                            cls.process_flow(name=o.name, op=operator)
                case 'BOOL_a':
                    text += cls.walk_criteria(o.op, o.operands, attr_set)
                case 'MATH_a':
                    text += cls.walk_criteria(o.op, o.operands, attr_set)
                case 'UNARY_a':
                    print()
        return text

    @classmethod
    def process(cls, mmdb: 'Tk', action_id: str, input_nsflow: Flow_ap, selection_parse: Selection_a,
                activity_data: Activity_ap):
        """
        Break down criteria into a set of attribute comparisons and validate the components of a Select Action that
        must be populated into the metamodel.
         | These components are:
        * Restriction Criterian (Comparison or Ranking)
        * Scalar Flow inputs to any Comparison Criterion

        Sift through criteria to ensure that each terminal is either an attribute, input flow, or value.
        :param mmdb:
        :param action_id:
        :param input_nsflow:
        :param activity_data:
        :param selection_parse:
        """
        cls.mmdb = mmdb
        cls.action_id = action_id
        cls.anum = activity_data.anum
        cls.domain = activity_data.domain

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
        Relvar.insert(relvar='Restriction_Condition', tuples=[
            Restriction_Condition_i(Action=cls.action_id, Activity=cls.anum, Domain=cls.domain,
                                    Expression=cls.expression, Selection_cardinality=cardinality
                                    )
        ])