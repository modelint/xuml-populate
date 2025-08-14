"""
create_action.py – Populate a create action in PyRAL
"""

# System
import logging
from typing import Any

# Model Integration
from scrall.parse.visitor import New_inst_a
from pyral.relation import Relation
from pyral.relvar import Relvar
from pyral.transaction import Transaction

# xUML populate
from xuml_populate.utility import print_mmdb
from xuml_populate.populate.actions.new_assoc_ref_action import NewAssociativeReferenceAction
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import ActivityAP, Boundary_Actions
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.mmclass_nt import (Create_Action_i, Instance_Initialization_i, Attribute_Initialization_i,
                                               Explicit_Initialization_i, Reference_Initialization_i,
                                               Default_Initialization_i, Local_Create_Action_i,
                                               Reference_Value_Input_i, Instance_Action_i)

_logger = logging.getLogger(__name__)

# Transactions
tr_Create = "Create Action"

class CreateAction:
    """
    Create all relations for a Create Action.
    """
    def __init__(self, statement_parse: New_inst_a, activity_data: ActivityAP):
        """
        Initialize with everything the Create Action requires

        Args:
            statement_parse: Parsed representation of the New Instance expression
            activity_data: Collected info about the activity
        """
        self.action_id = None
        self.activity_data = activity_data

        # Convenience
        self.anum = self.activity_data.anum
        self.domain = self.activity_data.domain
        self.signum = self.activity_data.signum
        self.to_ref_parse = statement_parse.rels

        # Unpack statement parse
        self.target_class = statement_parse.cname.name
        self.non_ref_ivalues: dict[str, Any] = {}

        self.non_ref_inits = statement_parse.attrs
        self.ref_inits = statement_parse.rels

        # We will use this nested dictionary to gather all required initial attribute values
        # for non referential attributes
        self.non_ref_ivalues: dict[str, dict[str, Any]] = {}

    def process(self) -> Boundary_Actions:
        """

        Returns:
            Boundary_Actions: The signal action id is both the initial and final action id
        """
        # Begin by populating the Action itself
        # Populate the Action superclass instance and obtain an action_id
        Transaction.open(db=mmdb, name=tr_Create)
        self.action_id = Action.populate(tr=tr_Create, anum=self.activity_data.anum, domain=self.activity_data.domain,
                                         action_type="create")  # Transaction open
        Relvar.insert(db=mmdb, tr=tr_Create, relvar='Create Action', tuples=[
            Create_Action_i(ID=self.action_id, Activity=self.activity_data.anum, Domain=self.activity_data.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Create, relvar='Instance Action', tuples=[
            Create_Action_i(ID=self.action_id, Activity=self.activity_data.anum, Domain=self.activity_data.domain)
        ])
        output_flow = Flow.populate_instance_flow(cname=self.target_class, anum=self.anum, domain=self.domain,
                                                  single=True)
        Relvar.insert(db=mmdb, tr=tr_Create, relvar='Local Create Action', tuples=[
            Local_Create_Action_i(ID=self.action_id, Activity=self.activity_data.anum, Domain=self.activity_data.domain,
                                  New_instance_flow=output_flow.fid)
        ])


        # When this class does not participate in any generalization, there is only one of these
        # TODO: Check for generalization
        Relvar.insert(db=mmdb, tr=tr_Create, relvar='Instance Initialization', tuples=[
            Instance_Initialization_i(Create_action=self.action_id, Class=self.target_class,
                                      Activity=self.activity_data.anum, Domain=self.activity_data.domain)
        ])

        # We need to verify that each attribute of the target class is initialized

        # Get all attribute names for the target class and split into referential and non-referential
        R = f"Class:<{self.target_class}>, Domain:<{self.domain}>"
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
                Attribute_Initialization_i(Create_action=self.action_id, Attribute=a, Class=self.target_class,
                                           Activity=self.activity_data.anum, Domain=self.activity_data.domain)
            ])

        # Populate Referential Initializations
        for r in ref_attr_names:
            Relvar.insert(db=mmdb, tr=tr_Create, relvar='Reference Initialization', tuples=[
                Reference_Initialization_i(Create_action=self.action_id, Attribute=r, Class=self.target_class,
                                           Activity=self.activity_data.anum, Domain=self.activity_data.domain)
            ])

        # Obtain initial values for each non-referential attribute as follows:
        # --
        # If an initial value is supplied in the statement, use it
        # Otherwise look for an initial default value
        # Failing that, look for a default value determined by the Scalar (type)
        # And if we still don't find a value (not all types provide a default) raise an exception

        # Process all explicit non referential attribute initializations
        for av_init in self.non_ref_inits:
            attr_name = av_init.attr.name
            sflow_name = av_init.scalar_expr
            sflow_source = type(sflow_name).__name__

            # The source of any Explicit Initialization, as described in the Create Delete Subsystem class model,
            # is either an input parameter flowing into the activity or a Scalar Flow generated
            # by some internal Action
            match sflow_source:
                case 'N_a':
                    # Labeled scalar flow output by some other action
                    pass  # TODO: Locate labeled flow
                case 'IN_a':
                    # Labeled scalar flow fed by an input parameter
                    R = f"Parameter:<{sflow_name.name}>, Signature:<{self.signum}>, Activity:<{self.anum}>, Domain:<{self.domain}>"
                    activity_input_r = Relation.restrict(db=mmdb, relation='Activity Input', restriction=R)
                    if len(activity_input_r.body) != 1:
                        msg = (f"Parameter input [{self.anum}:{sflow_name.name}] not found in metamodel db "
                               f"for {self.activity_data.activity_path}")
                        _logger.error(msg)
                        raise ActionException(msg)
                    # Get the corresponding parameter flow

                    activity_input_t = activity_input_r.body[0]  # The Activity Input instance tuple
                    # TODO: IMPORTANT Verify that parameter flow type matches the attribute type, else exception
                    Relvar.insert(db=mmdb, tr=tr_Create, relvar='Explicit Initialization', tuples=[
                        Explicit_Initialization_i(Create_action=self.action_id, Attribute=r, Class=self.target_class,
                                                  Activity=self.activity_data.anum, Domain=self.activity_data.domain,
                                                  Initial_value_flow=activity_input_t["Flow"])
                    ])
                case _:
                    pass

        # Now process each implicit initialization
        # Find all non referential attributes with no value explicitly specified, these will require default values
        default_init_attrs = [a for a, v in self.non_ref_ivalues.items() if not v]
        for da in default_init_attrs:
            R = f"Attribute:<{da}>, Class:<{self.target_class}>, Domain:<{self.domain}>"
            default_ival_r = Relation.restrict(db=mmdb, relation='Default Initial Value', restriction=R)
            if len(default_ival_r.body) == 1:
                # Indicate that there is a value available in the metamodel
                Relvar.insert(db=mmdb, tr=tr_Create, relvar='Default Initialization', tuples=[
                    Default_Initialization_i(Create_action=self.action_id, Attribute=r, Class=self.target_class,
                                             Activity=self.activity_data.anum, Domain=self.activity_data.domain,
                                             Initial_value_specified=True)
                ])
            else:
                Relvar.insert(db=mmdb, tr=tr_Create, relvar='Default Initialization', tuples=[
                    Default_Initialization_i(Create_action=self.action_id, Attribute=r, Class=self.target_class,
                                             Activity=self.activity_data.anum, Domain=self.activity_data.domain,
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
                msg2 = f"No explicit or default initial value defined for attribute {self.domain}:{self.target_class}.{da}"
                _logger.error(msg2)
                raise ActionException(msg2)


        # Now we need to obtain an input tuple flow for each linked relationship
        # So that all of the referential attributes can be initialized during model execution
        for to_ref in self.to_ref_parse:
            if to_ref.iset2:
                # There are two references on this linked relationship which means that
                # this relationship is associative -- one reference to each participating class
                ref_action = NewAssociativeReferenceAction(create_action_id=self.action_id, action_parse=to_ref,
                                                           activity_data=self.activity_data, tr=tr_Create)
                tuple_fid, ref_attr_names = ref_action.populate()
                for n in ref_attr_names:
                    Relvar.insert(db=mmdb, tr=tr_Create, relvar='Reference Value Input', tuples=[
                        Reference_Value_Input_i(Flow=tuple_fid, Create_action=self.action_id, Attribute=n,
                                                Class=self.target_class,
                                                Activity=self.activity_data.anum, Domain=self.activity_data.domain,
                                                )
                    ])
            else:
                pass
                # New simple ref action
            pass

        Transaction.execute(db=mmdb, name=tr_Create)

        return Boundary_Actions(ain={self.action_id}, aout={self.action_id})
