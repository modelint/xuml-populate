""" delegated_creation.py -- Populate a Delegated Creation Activity """

# System
import logging
from typing import TYPE_CHECKING
from collections import namedtuple

# Model Integration
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from pyral.relation import Relation
from scrall.parse.visitor import New_inst_a

# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.populate.mmclass_nt import Initialization_Source_i
from xuml_populate.populate.actions.create_action import CreateAction
from xuml_populate.populate.actions.new_assoc_ref_action import NewAssociativeReferenceAction
from xuml_populate.populate.actions.aparse_types import (DelegatedCreationActivityAP, Boundary_Actions,
                                                         New_delegated_inst, Flow_refs)
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.populate.flow import Flow
from xuml_populate.utility import print_mmdb
from xuml_populate.config import mmdb
from xuml_populate.exceptions.action_exceptions import *

_logger = logging.getLogger(__name__)

tr_DelCreate = "Delegated Creation Activity"

class DelegatedCreationActivity:
    """

    """

    def __init__(self, parse: New_inst_a, domain: str, delegating_activity: str,
                 attr_init_flows: dict[str, str],  ref_inits: dict[str, list[str]]):
        """

        """
        self.parse = parse
        self.class_name = parse.cname.name
        self.attr_init_flows = attr_init_flows
        self.ref_inits = ref_inits
        self.domain = domain
        self.delegating_anum = delegating_activity

        self.activity = None  # Assigned in populate
        self.anum = None  # Assigned in populate

        self.populate()

    def populate(self) -> Boundary_Actions:
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
        # Look up the Initial Pseudo State and get the associated activity number
        R = f"Class:<{self.class_name}>, Domain:<{self.domain}>"
        ip_state_r = Relation.restrict(db=mmdb, relation='Initial Pseudo State', restriction=R)
        if len(ip_state_r.body) != 1:
            msg = f"Single initial_pseudo_state Pseudo State for Lifecycle: [{self.class_name}] not defined in metamodel"
            _logger.error(msg)
            raise ActionException(msg)
        self.anum = ip_state_r.body[0]["Creation_activity"]
        # Create an activity object to provide data for instance set processing
        creation_activity_data = DelegatedCreationActivityAP(
            anum=self.anum, domain=self.domain, cname=self.class_name,
            activity_path=f"{self.domain}:{self.class_name}[initial pseudo state]")

        # Populate the State Activity Actions
        from xuml_populate.populate.activity import Activity
        self.activity = Activity(activity_data=creation_activity_data)

        Transaction.open(db=mmdb, name=tr_DelCreate)

        # Populate Initialization Source and Data Flows to mirror input from delegating source
        # Obtain a scalar flow for each attribute to be initialized
        for a in self.attr_init_flows:
            # This will be a set of attr name / scalar flow id pairs
            local_attr_flow = Flow.copy_data_flow(tr=tr_DelCreate, ref_fid=a, ref_anum=self.delegating_anum,
                                                  new_anum=self.anum, domain=self.domain)
            Relvar.insert(db=mmdb, tr=tr_DelCreate, relvar='Initialization Source', tuples=[
                Initialization_Source_i(Source_flow=a, Delegating_activity=self.delegating_anum,
                                        Creation_activity=self.anum, Domain=self.domain)
            ])
            # TODO: If delegated flows are unlabled, we should label the local flows to match the attr names
        rnum_refs = []
        for rel, refs in self.ref_inits.items():
            local_ref_flows = []
            for ref in refs:
                local_ref_flow = Flow.copy_data_flow(tr=tr_DelCreate, ref_fid=ref, ref_anum=self.delegating_anum,
                                                     new_anum=self.anum, domain=self.domain)
                local_ref_flows.append(local_ref_flow.fid)
                Relvar.insert(db=mmdb, tr=tr_DelCreate, relvar='Initialization Source', tuples=[
                    Initialization_Source_i(Source_flow=ref, Delegating_activity=self.delegating_anum,
                                            Creation_activity=self.anum, Local_flow=local_ref_flow, Domain=self.domain)
                ])
            rnum_refs.append(Flow_refs(rnum=rel.rnum, ref_flow1=refs[0], ref_flow2=None if len(refs) != 2 else refs[1]))
        new_inst = New_delegated_inst(cname=self.class_name, attr_flows=[], ref_flows=rnum_refs)

        # Now populate the creation action
        ca = CreateAction(statement_parse=new_inst, activity=self.activity)
        b = ca.process()
        return b  # TODO: Don't think these are ever needed since called by an external activity
        pass

