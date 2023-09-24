"""
select_action.py – Populate a selection action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING, Optional, Set
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap
from xuml_populate.exceptions.action_exceptions import ComparingNonAttributeInSelection, NoInputInstanceFlow
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.expressions.restriction_condition import RestrictCondition
from xuml_populate.populate.mmclass_nt import Select_Action_i, Single_Select_i, Identifier_Select_i, \
    Zero_One_Cardinality_Select_i, Many_Select_i, Restrict_Action_i, Restriction_Condition_i, \
    Equivalence_Criterion_i, Comparison_Criterion_i, Ranking_Criterion_i, Projected_Attribute_i, \
    Class_Restriction_Condition_i, Criterion_i
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction
from scrall.parse.visitor import N_a, BOOL_a, Op_a

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class SelectAction:
    """
    Create all relations for a Select Statement
    """

    input_instance_flow = None  # We are selecting instances from this instance flow
    output_instance_flow = None
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
    def populate_multiplicity_subclasses(cls):
        """
        Determine multiplicity of output and populate the relevant Select Action subclasses
        """
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
    def populate(cls, mmdb: 'Tk', input_instance_flow: Flow_ap, selection_parse, activity_data: Activity_ap) -> (
            str, Flow_ap, Set[Flow_ap]):
        """
        Populate the Select Statement

        :param mmdb:
        :param input_instance_flow: The source flow into this selection
        :param selection_parse:  The parsed Scrall select action group
        :param activity_data:
        :return: The select action id, the output flow, and any scalar flows input for attribute comparison
        """
        # Save attribute values that we will need when creating the various select subsystem
        # classes
        cls.mmdb = mmdb
        cls.domain = activity_data.domain
        cls.anum = activity_data.anum
        cls.activity_data = activity_data

        # Populate the Action superclass instance and obtain its action_id
        cls.action_id = Action.populate(cls.mmdb, cls.anum, cls.domain)  # Transaction open
        Relvar.insert(relvar='Select_Action', tuples=[
            Select_Action_i(ID=cls.action_id, Activity=cls.anum, Domain=cls.domain, Input_flow=input_instance_flow.fid)
        ])
        cls.selection_parse = selection_parse
        # Walk through the criteria parse tree storing any attributes or input flows
        # Also check to see if we are selecting on an identifier

        selection_cardinality, sflows = RestrictCondition.process(mmdb, action_id=cls.action_id,
                                                                  input_nsflow=input_instance_flow,
                                                                  selection_parse=selection_parse,
                                                                  activity_data=activity_data)

        Relvar.insert(relvar='Class_Restriction_Condition', tuples=[
            Class_Restriction_Condition_i(Select_action=cls.action_id, Activity=cls.anum, Domain=cls.domain)
        ])
        # Create output flows
        cls.populate_multiplicity_subclasses()

        # We now have a transaction with all select-action instances, enter into the metamodel db
        Transaction.execute()  # Select Action
        return cls.action_id, cls.output_instance_flow, sflows
