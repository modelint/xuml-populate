"""
create_action.py – Populate a create action in PyRAL
"""

# System
import logging
from typing import Any, Optional, TYPE_CHECKING, Self

# Model Integration
from scrall.parse.visitor import New_inst_a
from pyral.relation import Relation
from pyral.relvar import Relvar
from pyral.transaction import Transaction

# xUML populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.utility import print_mmdb
from xuml_populate.populate.actions.new_assoc_ref_action import NewAssociativeReferenceAction
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Boundary_Actions, New_delegated_inst
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.mmclass_nt import (Create_Action_i, Instance_Initialization_i, Attribute_Initialization_i,
                                               Explicit_Initialization_i, Reference_Initialization_i,
                                               Default_Initialization_i, Local_Create_Action_i,
                                               Reference_Value_Input_i, Instance_Action_i, Delegated_Create_Action_i)

_logger = logging.getLogger(__name__)

# Transactions
tr_Create = "Create Action"

class CreateAction:
    """
    Create all relations for a Create Action.
    """
    @classmethod
    def from_delegated(cls, new_inst: New_delegated_inst, activity: 'Activity') -> Self:
        """
        Args:
            new_inst:
            activity:

        Returns:
        """
        return cls(class_name=new_inst.cname, ref_isets=None, attr_exprs=None,
                   attr_flows=new_inst.attr_flows, ref_flows=new_inst.ref_flows, is_delegated=True, activity=activity)

    @classmethod
    def from_local(cls, statement_parse: New_inst_a, activity: 'Activity') -> Self:
        """
        Args:
            statement_parse: Parsed representation of the New Instance expression
            activity:

        Returns:
        """
        # Unpack the parse
        attr_exprs = {a.attr.name: a.scalar_expr for a in statement_parse.attrs}
        ref_isets = {r.rnum.rnum: [r.iset1] if r.iset2 is None else [r.iset1, r.iset2] for r in statement_parse.rels}
        # Provide exprs and isets since they must be resolved to flows locally
        return cls(class_name=statement_parse.cname.name, ref_isets=ref_isets, attr_exprs=attr_exprs,
                   attr_flows=None, ref_flows=None, is_delegated=False, activity=activity)

    def __init__(self, class_name: str, attr_exprs: dict[str, Any] | None, ref_isets: dict[str, list[Any]] | None,
                 attr_flows: dict[str, str] | None, ref_flows: dict[str, list[str]] | None, is_delegated: bool,
                 activity: 'Activity'):
        """
        Initialize with everything the Create Action requires

        Args:
            activity: Collected info about the activity
        """
        self.action_id = None
        self.activity = activity
        self.class_name = class_name
        self.is_delegated = is_delegated

        if is_delegated:
            self.attr_flows = attr_flows
            self.ref_flows = ref_flows
            self.attr_exprs = None
            self.ref_isets = None
        else:
            self.attr_flows = None
            self.ref_flows = None
            self.attr_exprs = attr_exprs
            self.ref_isets = ref_isets

        # We will use this nested dictionary to gather all required initial_pseudo_state attribute values
        # for non referential attributes
        # self.non_ref_ivalues: dict[str, Any] = {}
        # self.non_ref_ivalues: dict[str, dict[str, Any]] = {}

    def process(self) -> Boundary_Actions:
        """

        Returns:
            Boundary_Actions: The signal action id is both the initial_pseudo_state and final action id
        """
        # Begin by populating the Action itself
        # Populate the Action superclass instance and obtain an action_id
        Transaction.open(db=mmdb, name=tr_Create)
        self.action_id = Action.populate(tr=tr_Create, anum=self.activity.anum, domain=self.activity.domain,
                                         action_type="create")  # Transaction open
        Relvar.insert(db=mmdb, tr=tr_Create, relvar='Create Action', tuples=[
            Create_Action_i(ID=self.action_id, Activity=self.activity.anum, Domain=self.activity.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Create, relvar='Instance Action', tuples=[
            Create_Action_i(ID=self.action_id, Activity=self.activity.anum, Domain=self.activity.domain)
        ])
        if not self.is_delegated:
            output_flow = Flow.populate_instance_flow(cname=self.class_name, anum=self.activity.anum,
                                                      domain=self.activity.domain, single=True)
        else:
            output_flow = None

        if self.is_delegated:
            Relvar.insert(db=mmdb, tr=tr_Create, relvar='Delegated Create Action', tuples=[
                Delegated_Create_Action_i(ID=self.action_id, Activity=self.activity.anum, Domain=self.activity.domain)
            ])
        else:
            Relvar.insert(db=mmdb, tr=tr_Create, relvar='Local Create Action', tuples=[
                Local_Create_Action_i(ID=self.action_id, Activity=self.activity.anum, Domain=self.activity.domain,
                                      New_instance_flow=output_flow.fid)
            ])

        # When this class does not participate in any generalization, there is only one of these
        # TODO: Check for generalization
        Relvar.insert(db=mmdb, tr=tr_Create, relvar='Instance Initialization', tuples=[
            Instance_Initialization_i(Create_action=self.action_id, Class=self.class_name,
                                      Activity=self.activity.anum, Domain=self.activity.domain)
        ])

        # We need to verify that each attribute of the target class is initialized

        # Get all attribute names for the target class and split into referential and non-referential
        R = f"Class:<{self.class_name}>, Domain:<{self.activity.domain}>"
        Relation.restrict(db=mmdb, relation='Attribute', restriction=R, svar_name="attrs")
        attr_ref_r = Relation.semijoin(db=mmdb, rname2="Attribute Reference",
                                       attrs={"Name": "From_attribute", "Class": "From_class", "Domain": "Domain"})
        attr_names_r = Relation.project(db=mmdb, relation="attrs", attributes=("Name", "Scalar",),
                                        svar_name="attr_name_types")
        attr_names = {n["Name"] for n in attr_names_r.body}

        # These are the droids we're looking for
        ref_attr_names = {n["From_attribute"] for n in attr_ref_r.body}  # All of the referential attribute names
        non_ref_attr_names = attr_names - ref_attr_names  # All of the non referential attribute names

        # Populate all Attribute Initialization instances
        for a in attr_names:
            Relvar.insert(db=mmdb, tr=tr_Create, relvar='Attribute Initialization', tuples=[
                Attribute_Initialization_i(Create_action=self.action_id, Attribute=a, Class=self.class_name,
                                           Activity=self.activity.anum, Domain=self.activity.domain)
            ])

        # Populate Referential Initializations
        for r in ref_attr_names:
            Relvar.insert(db=mmdb, tr=tr_Create, relvar='Reference Initialization', tuples=[
                Reference_Initialization_i(Create_action=self.action_id, Attribute=r, Class=self.class_name,
                                           Activity=self.activity.anum, Domain=self.activity.domain)
            ])

        # Obtain initial_pseudo_state values for each non-referential attribute as follows:
        # --
        # If an initial_pseudo_state value is supplied in the statement, use it
        # Otherwise look for an initial_pseudo_state default value
        # Failing that, look for a default value determined by the Scalar (type)
        # And if we still don't find a value (not all types provide a default) raise an exception

        if self.is_delegated:
            for attr_name, attr_flow in self.attr_flows.items():
                Relvar.insert(db=mmdb, tr=tr_Create, relvar='Explicit Initialization', tuples=[
                    Explicit_Initialization_i(Create_action=self.action_id, Attribute=attr_name, Class=self.class_name,
                                              Activity=self.activity.anum, Domain=self.activity.domain,
                                              Initial_value_flow=attr_flow)
                ])
        else:
            # Process all explicit non referential attribute initializations
            for name, sexpr in self.attr_exprs.items():
                sflow_source = type(sexpr).__name__

                # The source of any Explicit Initialization, as described in the Create Delete Subsystem class model,
                # is either an input parameter flowing into the activity or a Scalar Flow generated
                # by some internal Action
                sexpr_type = type(sexpr).__name__
                match sexpr_type:
                    case 'N_a':
                        # Labeled scalar flow output by some other action
                        pass  # TODO: Locate labeled flow
                    case 'IN_a':
                        # Labeled scalar flow fed by an input parameter
                        R = (f"Parameter:<{sexpr.name}>, Signature:<{self.activity.signum}>, "
                             f"Activity:<{self.activity.anum}>, Domain:<{self.activity.domain}>")
                        activity_input_r = Relation.restrict(db=mmdb, relation='Activity Input', restriction=R)
                        if len(activity_input_r.body) != 1:
                            msg = (f"Parameter input [{self.activity.anum}:{sexpr.name}] not found in metamodel db "
                                   f"for {self.activity.activity_path}")
                            _logger.error(msg)
                            raise ActionException(msg)
                        # Get the corresponding parameter flow

                        activity_input_t = activity_input_r.body[0]  # The Activity Input instance tuple
                        # TODO: IMPORTANT Verify that parameter flow type matches the attribute type, else exception
                        Relvar.insert(db=mmdb, tr=tr_Create, relvar='Explicit Initialization', tuples=[
                            Explicit_Initialization_i(Create_action=self.action_id, Attribute=name, Class=self.class_name,
                                                      Activity=self.activity.anum, Domain=self.activity.domain,
                                                      Initial_value_flow=activity_input_t["Flow"])
                        ])
                    case _:
                        pass

        # Now process each implicit initialization
        # Find all non referential attributes with no value explicitly specified, these will require default values
        if self.is_delegated:
            default_init_attrs = non_ref_attr_names - set(self.attr_flows.keys())
        else:
            default_init_attrs = non_ref_attr_names - set(self.attr_exprs.keys())

        for da in default_init_attrs:
            R = f"Attribute:<{da}>, Class:<{self.class_name}>, Domain:<{self.activity.domain}>"
            default_ival_r = Relation.restrict(db=mmdb, relation='Default Initial Value', restriction=R)
            if len(default_ival_r.body) == 1:
                # Indicate that there is a value available in the metamodel
                Relvar.insert(db=mmdb, tr=tr_Create, relvar='Default Initialization', tuples=[
                    Default_Initialization_i(Create_action=self.action_id, Attribute=r, Class=self.class_name,
                                             Activity=self.activity.anum, Domain=self.activity.domain,
                                             Initial_value_specified=True)
                ])
            else:
                Relvar.insert(db=mmdb, tr=tr_Create, relvar='Default Initialization', tuples=[
                    Default_Initialization_i(Create_action=self.action_id, Attribute=r, Class=self.class_name,
                                             Activity=self.activity.anum, Domain=self.activity.domain,
                                             Initial_value_specified=False)
                ])
                # Last chance... Look for a default value defined on the Attribute's type
                # TODO: We'll need a populated type model so that we can search it
                R = f"Name:<{da}>"
                name_type_r = Relation.restrict(db=mmdb, relation="attr_name_types", restriction=R)
                scalar_type_name = name_type_r.body[0]["Scalar"]
                # For now, let's assume we did the search and didn't find one
                # We cannot find any value for the attribute so we cannot peform the create action
                msg1 = f"No type default defined on scalar type {scalar_type_name}"
                _logger.error(msg1)
                msg2 = (f"No explicit or default initial_pseudo_state value defined for "
                        f"attribute {self.domain}:{self.class_name}.{da}")
                _logger.error(msg2)
                raise ActionException(msg2)


        # Now we need to obtain an input tuple flow for each linked relationship
        # So that all of the referential attributes can be initialized during model execution
        if self.is_delegated:
            for rel in self.ref_flows:
                if rel.ref_flow2 is not None:
                    # There are two references on this linked relationship which means that
                    # this relationship is associative -- one reference to each participating class
                    ref_action = NewAssociativeReferenceAction.from_delegated(
                        tr=tr_Create, create_action_id=self.action_id, rnum=rel.rnum, ref_fid1=rel.ref_flow1,
                        ref_fid2=rel.ref_flow2, activity=self.activity
                    )
                    tuple_fid, ref_attr_names = ref_action.populate()
                    for n in ref_attr_names:
                        Relvar.insert(db=mmdb, tr=tr_Create, relvar='Reference Value Input', tuples=[
                            Reference_Value_Input_i(Flow=tuple_fid, Create_action=self.action_id, Attribute=n,
                                                    Class=self.class_name,
                                                    Activity=self.activity.anum, Domain=self.activity.domain,
                                                    )
                        ])

                pass

        else:
            for rnum, ref_isets in self.ref_isets.items():
                if len(ref_isets) == 2:
                    # There are two references on this linked relationship which means that
                    # this relationship is associative -- one reference to each participating class
                    ref_action = NewAssociativeReferenceAction.from_local(
                        tr=tr_Create, create_action_id=self.action_id,
                        rnum=rnum, ref1=ref_isets[0], ref2=ref_isets[1],
                        activity=self.activity
                    )
                    tuple_fid, ref_attr_names = ref_action.populate()
                    for n in ref_attr_names:
                        Relvar.insert(db=mmdb, tr=tr_Create, relvar='Reference Value Input', tuples=[
                            Reference_Value_Input_i(Flow=tuple_fid, Create_action=self.action_id, Attribute=n,
                                                    Class=self.class_name,
                                                    Activity=self.activity.anum, Domain=self.activity.domain,
                                                    )
                        ])
                else:
                    pass
                    # New simple ref action
                pass

        Transaction.execute(db=mmdb, name=tr_Create)

        return Boundary_Actions(ain={self.action_id}, aout={self.action_id})
