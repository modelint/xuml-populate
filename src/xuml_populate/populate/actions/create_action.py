"""
create_action.py – Populate a create action in PyRAL
"""

# System
import logging
from typing import Sequence, Tuple, Optional, Any

# Model Integration
from scrall.parse.visitor import New_inst_a, Scalar_RHS_a
from pyral.relation import Relation
from pyral.relvar import Relvar
from pyral.transaction import Transaction

# xUML populate
from xuml_populate.utility import print_mmdb
from xuml_populate.populate.actions.expressions.scalar_expr import ScalarExpr
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, ActivityAP, Boundary_Actions, SMType
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.mmclass_nt import (
    Create_Action_i, Instance_Initialization_i, Attribute_Initialization_i, Explicit_Initialization_i,
    Reference_Initialization_i, Default_Initialization_i, Initializing_Attribute_Reference_i,
    Initializing_Instance_Reference_i, Local_Create_Action_i, New_Instance_Flow_i
)

_logger = logging.getLogger(__name__)

# Transactions
tr_Create = "Create Action"

class CreateAction:
    """
    Create all relations for a Create Action.
    """
    def __init__(self, statement_parse: New_inst_a, activity_data: ActivityAP):
        """
        Initialize with everything the Signal statement requires

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
        non_ref_attr_names = attr_names - ref_attr_names  # All of the non referentila attribute names

        # Set the initial value for each non referential attribute to {} until we determine
        # its source (flow, attribute or type default)
        # We will raise an exception if we can't fill all of those empty subdicts
        self.non_ref_ivalues = {a: {} for a in non_ref_attr_names}

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
                    R = f"Name:<{sflow_name.name}>, Signature:<{self.signum}>, Domain:<{self.domain}>"
                    parameter_r = Relation.restrict(db=mmdb, relation='Parameter', restriction=R)
                    if len(parameter_r.body) != 1:
                        msg = (f"State signature parameter [{sflow_name.name}] not found in metamodel db "
                               f"for {self.activity_data.activity_path}")
                        _logger.error(msg)
                        raise ActionException(msg)
                    parameter_t = parameter_r.body[0]  # The Parameter instance tuple
                    # TODO: IMPORTANT Verify that parameter flow type matches the attribute type, else exception
                    self.non_ref_ivalues[attr_name] = {'flow': parameter_t["Input_flow"]}
                case _:
                    pass
        # Now process each implicit initialization
        # Find all non referential attributes with no value explicitly specified, these will require default values
        default_init_attrs = [a for a, v in self.non_ref_ivalues.items() if not v]
        for da in default_init_attrs:
            R = f"Attribute:<{da}>, Class:<{self.target_class}>, Domain:<{self.domain}>"
            default_ival_r = Relation.restrict(db=mmdb, relation='Default Initial Value', restriction=R)
            if len(default_ival_r.body) == 1:
                # There is a default initial value specified in the class model
                default_ival_t = default_ival_r.body[0]
                default_initial_value = default_ival_t["Value"]
                self.non_ref_ivalues[da] = {'default initial value': default_initial_value}
            else:
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

        # Now we need to find a value for each referential attribute
        # We'll do this by populating the relevant actions in the ref subsystem

        # Populate the Action superclass instance and obtain its action_id
        Transaction.open(db=mmdb, name=tr_Create)
        self.action_id = Action.populate(tr=tr_Create, anum=self.activity_data.anum, domain=self.activity_data.domain,
                                         action_type="create")  # Transaction open
        Relvar.insert(db=mmdb, tr=tr_Create, relvar='Create Action', tuples=[
            Create_Action_i(ID=self.action_id, Activity=self.activity_data.anum, Domain=self.activity_data.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Create, relvar='Signal Instance Set Action', tuples=[
            Local_Create_Action_i(ID=self.action_id, Activity=self.activity_data.anum, Domain=self.activity_data.domain)
        ])
        # Initialize all non-referential attributes
        for i in self.non_ref_inits:
            pass

        Transaction.execute(db=mmdb, name=tr_Create)
        return Boundary_Actions(ain={self.action_id}, aout={self.action_id})
