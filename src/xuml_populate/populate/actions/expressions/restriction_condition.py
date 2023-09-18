"""
restrict_action.py – Populate a Restrict Action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING, Optional
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap
from xuml_populate.exceptions.action_exceptions import ComparingNonAttributeInSelection, NoInputInstanceFlow
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Select_Action_i, Single_Select_i, Identifier_Select_i, \
    Zero_One_Cardinality_Select_i, Many_Select_i, Restrict_Action_i, Restriction_Condition_i, \
    Equivalence_Criterion_i, Comparison_Criterion_i, Ranking_Criterion_i, Projected_Attribute_i, \
    Class_Restriction_Condition_i, Criterion_i, Relational_Action_i, Table_Action_i
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction
from scrall.parse.visitor import N_a, BOOL_a, Op_a, Selection_a

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class RestrictAction:
    """
    Create all relations for a Restrict Action
    """

    input_relation_flow = None  # We are selecting tuples from this table flow
    output_relation_flow = None
    anum = None
    expression = None
    comparison_criteria = []
    equivalence_criteria = []
    restriction_text = ""
    cardinality = None
    action_id = None
    domain = None  # in this domain
    mmdb = None  # The database
    criterion_ctr = 0
    max_mult = None
    activity_data = None

    @classmethod
    def pop_restriction_criterion(cls, attr: str) -> int:
        cls.criterion_ctr += 1
        criterion_id = cls.criterion_ctr
        Relvar.insert(relvar='Criterion', tuples=[
            Criterion_i(ID=criterion_id, Action=cls.action_id, Activity=cls.anum, Attribute=attr,
                        Non_scalar_type=cls.input_instance_flow.tname, Domain=cls.domain)
        ])
        return criterion_id

    @classmethod
    def identifier_selection(cls) -> int:
        """
        | Determine whether we are selecting based on an identifier match.
        An identifier match supplies one value per identifier attribute for some identifier defined on
        the class.
         | Each comparison must be == (equivalence)
         |
         | **For example:**
         |
         | Assume Floor, Shaft is an identifier defined on the Accessible Shaft Level class
         | This means that if you supply a value for each attribute like so
         |
         | Accessible Shaft Level( Floor == x, Shaft == y )
         |
         | you will select at most one instance. But if you select based on:
         |
         | Accessible Shaft Level( Shaft == y )
         |
         | you may select multiple instances since a Shaft intersects multiple Floors
         :returns: An identifier number 1,2, ... or 0 if none found
        """
        idcheck = {c['attr'] for c in cls.comparison_criteria if c['op'] == '=='}
        R = f"Class:<{cls.input_instance_flow.tname}>, Domain:<{cls.domain}>"
        Relation.restrict(cls.mmdb, relation='Identifier_Attribute', restriction=R)
        Relation.project(cls.mmdb, attributes=('Identifier', 'Attribute',), svar_name='all_id_attrs')
        # We have created a named relation with a projection of each id_attr and its id_num
        # Now we must step through each id_num to see if we are selecting on any of them
        i = 1  # Start with inum 1 {I}, (identifier 1). Every class has at least this identifier
        while True:
            # Step through every identifier of the class and see if there is a set of equivalence
            # comparisons that forms a superset of this identifier. If we are selecting at most one instance
            R = f"Identifier:<{str(i)}>"
            t_id_n_attrs = Relation.restrict(cls.mmdb, relation='all_id_attrs', restriction=R)
            if not t_id_n_attrs.body:
                # This i num is not defined on the class, no more i nums to check
                break
            t_id_n_attr_names = Relation.project(cls.mmdb, attributes=('Attribute',))
            id_n_attr_names = {t['Attribute'] for t in t_id_n_attr_names.body}
            if not id_n_attr_names - idcheck:
                # The set of identifier attributes for the current id number
                # is present in the set of attribute equivalence matches
                # So we are selecting on an identifier and at most one instance can flow out of the selection
                return i
            i += 1  # Increment to the next I num (I1, I2, etc)
        return 0

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
        Validate that attribute is a member of the input flow class

        :param op:
        :param name:
        :return:
        """
        R = f"Name:<{name}>, Class:<{cls.input_instance_flow.tname}>, Domain:<{cls.domain}>"
        result = Relation.restrict(cls.mmdb, relation='Attribute', restriction=R)
        if not result.body:
            raise ComparingNonAttributeInSelection(f"select action restriction on class"
                                                   f"[{cls.input_instance_flow.tname}] is "
                                                   f"comparing on name [{name}] that is not an attribute of that class")
        cls.comparison_criteria.append({'attr': name, 'op': op})
        cls.attr_set = True

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
    def process_criteria(cls, criteria):
        """
        Break down criteria into a set of attribute comparisons and validate the components of a Select Action that
        must be populated into the metamodel.
         | These components are:
        * Restriction Criterian (Comparison or Ranking)
        * Scalar Flow inputs to any Comparison Criterion

        Sift through criteria to ensure that each terminal is either an attribute, input flow, or value.
        :param criteria:
        """
        # Consider case where there is a single boolean value critieria such as:
        #   shaft aslevs( Stop requested )
        # The implication is that we are selecting on: Stop requested == true
        # So elaborate the parse elminating our shorhand
        if type(criteria).__name__ == 'N_a':
            # Name only (no explicit operator or operand)
            criteria = BOOL_a(op='==', operands=[criteria, N_a(name='true')])
        # Walk the parse tree and save all attributes, ops, values, and input scalar flows
        cls.expression = cls.walk_criteria(criteria.op, criteria.operands)
        # Populate the Restriction Condition class
        Relvar.insert(relvar='Class_Restriction_Condition', tuples=[
            Class_Restriction_Condition_i(Select_action=cls.action_id, Activity=cls.anum, Domain=cls.domain)
        ])
        Relvar.insert(relvar='Restriction_Condition', tuples=[
            Restriction_Condition_i(Action=cls.action_id, Activity=cls.anum, Domain=cls.domain,
                                    Expression=cls.expression, Selection_cardinality=cls.cardinality
                                    )
        ])

        # Determine if this should be an Identifier Select subclass that yields at most one instance
        selection_idnum = cls.identifier_selection()
        if selection_idnum or cls.cardinality == 'ONE':
            cls.max_mult = MaxMult.ONE
            # Populate a single instance flow for the selection output
            output_fid = Flow.populate_instance_flow(cls.mmdb, cname=cls.input_instance_flow.tname,
                                                     activity=cls.anum, domain=cls.domain,
                                                     label=None, single=True)
            cls.output_instance_flow = Flow_ap(fid=output_fid, content=Content.INSTANCE,
                                               tname=cls.input_instance_flow.tname, max_mult=cls.max_mult)
            _logger.info(f"INSERT Select action output single instance Flow: [{cls.domain}:"
                         f"{cls.input_instance_flow.tname}:{cls.activity_data.activity_path.split(':')[-1]}"
                         f":{cls.output_instance_flow}]")
            # Populate the Single Select subclass
            Relvar.insert(relvar='Single_Select', tuples=[
                Single_Select_i(ID=cls.action_id, Activity=cls.anum, Domain=cls.domain,
                                Output_flow=cls.output_instance_flow.fid)
            ])
            if selection_idnum:
                # Populate an Identifier Select subclass
                Relvar.insert(relvar='Identifier_Select', tuples=[
                    Identifier_Select_i(ID=cls.action_id, Activity=cls.anum, Domain=cls.domain,
                                        Identifier=selection_idnum, Class=cls.input_instance_flow.tname)
                ])
            else:
                # Populate an Identifier Select subclass
                # Note that if both ONE cardinality specified and identifier select, identifier select takes precedence
                Relvar.insert(relvar='Zero_One_Cardinality_Select', tuples=[
                    Zero_One_Cardinality_Select_i(ID=cls.action_id, Activity=cls.anum, Domain=cls.domain)
                ])
        else:
            # Many select with Multiple Instance Flow output
            cls.max_mult = MaxMult.MANY
            cls.output_instance_flow = Flow.populate_instance_flow(cls.mmdb, cname=cls.input_instance_flow.tname,
                                                                   activity=cls.anum,
                                                                   domain=cls.domain, label=None, single=False)
            _logger.info(f"INSERT Select action output multiple instance Flow: [{cls.domain}:"
                         f"{cls.input_instance_flow.tname}:{cls.activity_data.activity_path.split(':')[-1]}"
                         f":{cls.output_instance_flow}]")
            # Populate the Many Select subclass
            Relvar.insert(relvar='Many_Select', tuples=[
                Many_Select_i(ID=cls.action_id, Activity=cls.anum, Domain=cls.domain,
                              Output_flow=cls.output_instance_flow.fid)
            ])

    @classmethod
    def populate(cls, mmdb: 'Tk', input_relation_flow: Flow_ap, selection_parse: Selection_a,
                 activity_data: Activity_ap) -> ( str, Flow_ap):
        """
        Populate the Restrict Action

        :param mmdb:
        :param input_relation_flow: The source table flow into this restriction
        :param selection_parse:  The parsed Scrall select action group
        :param activity_data:
        :return: The restrict action id and the output flow
        """
        # Save attribute values that we will need when creating the various select subsystem
        # classes
        cls.mmdb = mmdb
        cls.domain = activity_data.domain
        cls.anum = activity_data.anum
        cls.activity_data = activity_data

        # Here we convert from scrall parse '1', 'M' notation to user friendly 'ONE', 'ALL'
        # If 1, user wants at most one arbitrary instance, even if many are selected
        # If M, get them all.
        # TODO: Update scrall parser to yield these values
        cls.cardinality = 'ONE' if selection_parse.card == '1' else 'ALL'

        cls.input_relation_flow = input_relation_flow

        # Populate the Action superclass instance and obtain its action_id
        cls.action_id = Action.populate(cls.mmdb, cls.anum, cls.domain)  # Transaction open
        cls.selection_parse = selection_parse
        # Walk through the critieria parse tree storing any attributes or input flows
        # Also check to see if we are selecting on an identifier
        cls.process_criteria(criteria=selection_parse.criteria)

        Relvar.insert(relvar='Relational_Action', tuples=[
            Relational_Action_i(ID=cls.action_id, Activity=cls.anum, Domain=cls.domain)
        ])
        Relvar.insert(relvar='Table_Action', tuples=[
            Table_Action_i(ID=cls.action_id, Activity=cls.anum, Domain=cls.domain,
                           Input_a_flow=cls.input_relation_flow.fid, Output_flow=cls.output_relation_flow.fid)
        ])
        Relvar.insert(relvar='Restrict_Action', tuples=[
            Select_Action_i(ID=cls.action_id, Activity=cls.anum, Domain=cls.domain,
                            Input_flow=cls.input_relation_flow.fid)
        ])
        # We now have a transaction with all select-action instances, enter into the metamodel db
        Transaction.execute()  # Restrict Action
        return cls.action_id, cls.output_relation_flow