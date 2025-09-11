"""
select_action.py – Populate a selection action instance in PyRAL
"""
# System
import logging
from typing import List, TYPE_CHECKING

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.utility import print_mmdb
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Attribute_Comparison
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.actions.expressions.restriction_condition import RestrictCondition
from xuml_populate.populate.mmclass_nt import (Select_Action_i, Single_Select_i, Identifier_Select_i,
                                               Zero_One_Cardinality_Select_i, Many_Select_i,
                                               Class_Restriction_Condition_i, Instance_Action_i)
_logger = logging.getLogger(__name__)

# Transactions
tr_Select = "Select Action"


class SelectAction:
    """
    Create all relations for a Select Statement
    """

    def __init__(self, input_instance_flow: Flow_ap, selection_parse, activity: 'Activity',
                 hop_to_many_assoc_from_one_instance: bool = False):
        """

        Args:
            input_instance_flow:
            selection_parse:
            activity:
            hop_to_many_assoc_from_one_instance: Even though we are hopping into a many associative association
                class from a single instance, we still have multiple target instances to select from
                due to the many associative multiplicity. False if not hopping to a many associative association
                class and also False if hopping from multiple instances into a many associative association class.
        """
        self.hop_to_many_assoc_from_one_instance = hop_to_many_assoc_from_one_instance
        self.input_instance_flow = input_instance_flow  # We are selecting instances from this instance flow
        self.selection_parse = selection_parse
        self.activity = activity
        self.domain = activity.domain
        self.anum = activity.anum

        self.attr_comparisons: List[Attribute_Comparison]

        self.expression = None
        self.comparison_criteria = []
        self.equivalence_criteria = []
        self.restriction_text = ""
        self.criterion_ctr = 0
        self.max_mult: MaxMult
        self.rcond = None  # Assigned after restriction condition populated

        # Save attribute values that we will need when creating the various select subsystem
        # classes

        # Populate the Action superclass instance and obtain its action_id
        Transaction.open(db=mmdb, name=tr_Select)
        self.action_id = Action.populate(tr=tr_Select, anum=self.anum, domain=self.domain,
                                         action_type="select")  # Transaction open
        Relvar.insert(db=mmdb, tr=tr_Select, relvar='Instance Action', tuples=[
            Instance_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Select, relvar='Select Action', tuples=[
            Select_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                            Input_flow=self.input_instance_flow.fid)
        ])
        # Walk through the criteria parse tree storing any attributes or input flows
        # Also check to see if we are selecting on an identifier
        self.rcond = RestrictCondition(tr=tr_Select, action_id=self.action_id,
                                  input_nsflow=self.input_instance_flow,
                                  selection_parse=self.selection_parse,
                                  activity=self.activity,
                                  )
        # TODO Consolidate the four lines below, self.rcond is probably all we need
        # id_attrs_in_selection = rcond.identifier_attrs
        self.attr_comparisons = self.rcond.comparison_criteria
        self.selection_cardinality = self.rcond.cardinality
        self.sflows = self.rcond.input_scalar_flows

        Relvar.insert(db=mmdb, tr=tr_Select, relvar='Class Restriction Condition', tuples=[
            Class_Restriction_Condition_i(Select_action=self.action_id, Activity=self.anum, Domain=self.domain)
        ])
        # Create output flows
        self.max_mult, self.output_instance_flow = self.populate_multiplicity_subclasses()

        # We now have a transaction with all select-action instances, enter into the metamodel db
        Transaction.execute(db=mmdb, name=tr_Select)  # Select Action

    def identifier_selection(self) -> int:
        """
        Determine whether we are selecting an instance of a Class based on an identifier match.

        There are two cases of identifier selection to consider each of which yields a single instance flow output.

        Normally, we select an instance using a supplied identifier. The identifier ensures that
        at most one instance will be selected. Here we verify that each attribute of some identifier of the target
        class is compared using the == operator to a supplied value.

        But there is a more nuancd case to consider where we traverse to a many associative class from
        a single instance of either participating class. We set the self.hop_to_many_assoc_from_one_instance
        boolean to true during initialization when this case is detected.

        The normal and nuanced cases are mutually exclusive.

        Let's examine both of these cases with examples from the Elevator Case Study class model.

        In the normal case, the user wants to select a single instance using an identifier for the associated class.

        Assume Floor, Shaft is an identifier defined on the Accessible Shaft Level class
        This means that if you supply a value for each identifier attribute like so

        Accessible Shaft Level( Floor == x, Shaft == y )

        you will select at most one instance. But if you select based on only part of an identifier:

        Accessible Shaft Level( Shaft == y )

        you may select multiple instances since a Shaft intersects multiple Floors.

        The nuanced case applies when we select from a many associative class and when we have traversed to that class
        from a single participating instance flow. With a one associative class, this traversal will always direct us
        to at most a single instance without the specification of any identifier values. But the many associative case,
        by its very nature, leaves open the possibility of multiple instances. To narrow down to a single instance, the
        user must supply a value for each identifier attribute that is NOT itself a referential attribute formalizing
        the many associative relationship.

        For example, let's say that the user traverses from a single instance of Accessible Shaft Level,
        which happens to be a participating class on a many associative relationship. This relationship is
        formalized by the Floor Service class, which uses its non-referential 'Direction' identifier attribute to
        discriminate between an up or down call direction.

        If the Floor Service instance is selected using the == comparison on that 'Direction' attribute, we know
        that at most one instance will be selected. This is because the 'Direction' attribute is part of an Identifier,
        actually it is part of two Identifiers! But one is enough. It turns out that all of the other attributes of
        either of these two Identifiers are referential attributes formalizing the many associative relationship.

        Returns:
            In either case, normal or nuanced, we'll return the lowest numbered identifier that satisfies
                the condition. If the identity selection criteria is not met, we'll return 0 to indicate
                that no identifier match was found.
        """
        # Let's check to see if this is the nuanced case described above first
        # If so, we'll do some setup before iterating through the target class's identifiers
        if self.hop_to_many_assoc_from_one_instance:
            # Get the many associative rel name
            R = f"Class:<{self.input_instance_flow.tname}>, Domain:<{self.domain}>"
            assoc_class_r = Relation.restrict(db=mmdb, relation="Association Class", restriction=R)

            # Verify this is in fact a formalizing many associative class
            if not assoc_class_r.body:
                msg = f"Formalizing many associative class {self.input_instance_flow.tname} not populated"
                _logger.error(msg)
                raise ActionException(msg)
            if assoc_class_r.body[0]["Multiplicity"] != 'M':
                msg = (f"Expected formalizing many associative class {self.input_instance_flow.tname} but multiplicity"
                       f"is not M")
                _logger.error(msg)
                raise ActionException(msg)

            # Now let's create a set of all referential attribute components of the identifier
            # so that we can remove them from consideration when we iterate through the class'es identifiers
            # futher down
            attr_ref_r = Relation.semijoin(db=mmdb, rname2="Attribute Reference", attrs={
                "Class": "From_class", "Domain": "Domain", "Rnum": "Rnum"
            })
            many_assoc_ref_attrs = {a["From_attribute"] for a in attr_ref_r.body}

        # There is some further setup required for both the normal and nuanced cases here

        # Get all attributes comparing to a supplied value with == operator
        idcheck = {c.attr for c in self.attr_comparisons if c.op == '=='}

        # Do idcheck attrs constitute an identifier of the target class?
        R = f"Class:<{self.input_instance_flow.tname}>, Domain:<{self.domain}>"
        Relation.restrict(db=mmdb, relation='Identifier Attribute', restriction=R)
        Relation.project(db=mmdb, attributes=('Identifier', 'Attribute',), svar_name='all_id_attrs')
        # We have created a named relation with a projection of each id_attr and its id_num

        # Now we must step through each id_num to see if we are selecting on any of them
        i = 1  # Start with inum 1 {I}, (identifier 1). Every class has at least this identifier
        while True:
            # Step through every identifier of the class and see if there is a set of equivalence
            # comparisons that forms a superset of this identifier. If we are selecting at most one instance
            R = f"Identifier:<{str(i)}>"
            t_id_n_attrs = Relation.restrict(db=mmdb, relation='all_id_attrs', restriction=R)
            if not t_id_n_attrs.body:
                # This i num is not defined on the class, no more i nums to check
                if i == 1:
                    # Shlaer Mellor rules require that every class has at least one identifier
                    msg = f"No identifier defined for class {self.input_instance_flow.tname}"
                    _logger.error(msg)
                    raise ActionException(msg)
                # There are no more identifiers past or including the 2nd, so we end our search
                return 0

            # We create a set of all of the identifier attributes for the ID selected when we broke out of the loop
            t_id_n_attr_names = Relation.project(db=mmdb, attributes=('Attribute',))
            id_n_attr_names = {t['Attribute'] for t in t_id_n_attr_names.body}

            if self.hop_to_many_assoc_from_one_instance:
                # Nuanced selection case

                # We perform a set subtraction, removing all referential attributes that formalize the
                # many-associative relationship and compare the result with the id attributes we were selecting
                # in our selection/restriction criteria.
                # If the sets match, then we are selecting at most one unique instance on the current identifier number
                if id_n_attr_names - many_assoc_ref_attrs == idcheck:
                    return i
            else:
                # Normal id selection case
                if not id_n_attr_names - idcheck:
                    # The set of identifier attributes for the current id number
                    # is present in the set of attribute equivalence matches
                    # So we are selecting on an identifier and at most one instance can flow out of the selection
                    return i
            i += 1  # Increment to the next I num (I1, I2, etc)


    def populate_multiplicity_subclasses(self) -> tuple[MaxMult, Flow_ap]:
        """
        Determine multiplicity of output and populate the relevant Select Action subclasses
        """
        # Determine if this should be an Identifier Select subclass that yields at most one instance
        selection_idnum = self.identifier_selection()
        if selection_idnum or self.selection_cardinality == 'ONE':
            max_mult = MaxMult.ONE
            # Populate a single instance flow for the selection output
            output_instance_flow = Flow.populate_instance_flow(
                cname=self.input_instance_flow.tname, anum=self.anum, domain=self.domain,
                label=None, single=True
            )
            _logger.info(f"INSERT Select action output single instance Flow: [{self.domain}:"
                         f"{self.input_instance_flow.tname}:{self.activity.activity_path.split(':')[-1]}"
                         f":{output_instance_flow}]")
            # Populate the Single Select subclass
            Relvar.insert(db=mmdb, tr=tr_Select, relvar='Single_Select', tuples=[
                Single_Select_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                                Output_flow=output_instance_flow.fid)
            ])
            if selection_idnum:
                # Populate an Identifier Select subclass
                Relvar.insert(db=mmdb, tr=tr_Select, relvar='Identifier_Select', tuples=[
                    Identifier_Select_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                                        Identifier=selection_idnum, Class=self.input_instance_flow.tname)
                ])
            else:
                # Populate an Identifier Select subclass
                # Note that if both ONE cardinality specified and identifier select, identifier select takes precedence
                Relvar.insert(db=mmdb, tr=tr_Select, relvar='Zero_One_Cardinality_Select', tuples=[
                    Zero_One_Cardinality_Select_i(ID=self.action_id, Activity=self.anum, Domain=self.domain)
                ])
        else:
            # Many select with Multiple Instance Flow output
            max_mult = MaxMult.MANY
            output_instance_flow = Flow.populate_instance_flow(
                cname=self.input_instance_flow.tname, anum=self.anum,
                domain=self.domain, label=None, single=False
            )
            _logger.info(f"INSERT Select action output multiple instance Flow: [{self.domain}:"
                         f"{self.input_instance_flow.tname}:{self.activity.activity_path.split(':')[-1]}"
                         f":{output_instance_flow}]")
            # Populate the Many Select subclass
            Relvar.insert(db=mmdb, tr=tr_Select, relvar='Many_Select', tuples=[
                Many_Select_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                              Output_flow=output_instance_flow.fid)
            ])
        return max_mult, output_instance_flow
