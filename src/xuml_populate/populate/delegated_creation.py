""" delegated_creation.py -- Populate a Delegated Creation Activity """

# System
import logging
from typing import TYPE_CHECKING

# Model Integration
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from pyral.relation import Relation
from scrall.parse.visitor import New_inst_a

# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.populate.mmclass_nt import Delegated_Create_Action_i
from xuml_populate.populate.actions.create_action import CreateAction
from xuml_populate.populate.actions.new_assoc_ref_action import NewAssociativeReferenceAction
from xuml_populate.populate.actions.aparse_types import DelegatedCreationActivityAP
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.utility import print_mmdb
from xuml_populate.config import mmdb
from xuml_populate.exceptions.action_exceptions import *

class DelegatedCreationActivity:
    """

    """

    def __init__(self, parse: New_inst_a, domain: str):
        """

        """
        self.parse = parse
        self.domain = domain

        self.populate()

    def populate(self):
        """

        Returns:
        """
        """
        We populate this signal a bit differently
        1. We don't have a target instance set, we have a target lifecycle state machine (class)
        2. In that target lifecycle we need to populate a Delegated Creation Activity associated with an
           Initial Pseudo State
        3. We'll need to find any scalar flows or reference flows required for intialization
        4. And then we'll create a python object DelegatedCreationActivity, and it the flows and let it
           populate itself
        5. Finally, we instantiate our signal instance
        """
        pass
        # target_class = self.parse.cname.name
        # # Get the activity number of the Delegated Creation Activity for that lifecycle
        # R = f"Class:<{target_class}>, Domain:<{self.domain}>"
        # ip_state_r = Relation.restrict(db=mmdb, relation='Initial Pseudo State', restriction=R)
        # if len(ip_state_r.body) != 1:
        #     msg = f"Single initial_pseudo_state Pseudo State for Lifecycle: [{target_class}] not defined in metamodel"
        #     _logger.error(msg)
        #     raise ActionException(msg)
        # dc_anum = ip_state_r.body[0]["Creation_activity"]
        # # Create an activity object to provide data for instance set processing
        # creation_activity_data = DelegatedCreationActivityAP(
        #     anum=dc_anum, domain=self.domain, cname=target_class,
        #     activity_path=f"{self.domain}:{target_class}[initial pseudo state]")
        #
        # # Populate the State Activity Actions
        # from xuml_populate.populate.activity import Activity
        # creation_activity_obj = Activity(activity_data=creation_activity_data)
        # pass
        # # Obtain a scalar flow for each attribute to be initialized
        # for a in self.parse.attrs:
        #     # This will be scalar expressions each producing a scalar flow
        #     # Each consists of an attribute name and a scalar expr
        #     # TODO: Add this when we have an example
        #     pass
        # for r in self.parse.rels:
        #     # For each rel, we have either one (simple assoc) or two refs (associative)
        #     rnum = r.rnum
        #     iset = InstanceSet(input_instance_flow=None, iset_components=[r.iset1],
        #                        activity=creation_activity_obj)  # Important: All iset flows belong to Delegated Creation Activity
        #     # TODO: problem -- dc_anum needs to be the activity object, not just the name
        #     ain, aout, dest_flow = iset.process()
        #     pass
