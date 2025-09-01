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
    An activity has populated a delegated creation signal in some source activity and here we
    populate the creation activity associated with a corresponding event on an initial psuedo state transition.
    """

    def __init__(self, class_name: str, attr_init_flows: dict[str, str],  ref_inits: dict[str, list[str]],
                 delegating_activity: 'Activity'):
        """
        Gather the data from the delegating signal and then initiate the population of the creation
        activity.

        The delegating activity will have resolved all expressions into associated flows.
        We'll need to make a copy of each such flow locally as an Initialization Source.
        (See the Activity Subsystem class model)

        Args:
            class_name: We are creating an instance of this class
            attr_init_flows: Attribute name, flow id pairs from delegating activity
            ref_inits: List of one or two refs for each rnum from delegating activity
            delegating_activity: The activity obj where the delegating signal emanates
        """
        # From input params
        self.class_name = class_name
        self.attr_init_flows = attr_init_flows
        self.ref_inits = ref_inits
        self.domain = delegating_activity.domain
        self.delegating_anum = delegating_activity.anum

        # Determined while populating
        self.activity: str = ""
        self.anum: str = ""

        self.populate()

    def populate(self):
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

        # Gather activity data and create an activity object for our delegated creation activity
        creation_activity_data = DelegatedCreationActivityAP(
            anum=self.anum, domain=self.domain, cname=self.class_name,
            activity_path=f"{self.domain}:{self.class_name}[initial pseudo state]")
        from xuml_populate.populate.activity import Activity
        self.activity = Activity(activity_data=creation_activity_data)

        # Open a db population transaction enveloping all actions of this activity
        Transaction.open(db=mmdb, name=tr_DelCreate)

        # Mirror any attribute initialization flows from the delegating activity
        local_attr_flows: dict[str, str] = {}
        for attr_name, source_fid in self.attr_init_flows.items():
            # TODO: Think about how we want to label this flow
            source_label = Flow.lookup_label(fid=source_fid, anum=self.delegating_anum, domain=self.domain)
            local_attr_flow = Flow.copy_data_flow(ref_fid=source_fid, ref_anum=self.delegating_anum,
                                                  new_anum=self.anum, domain=self.domain, label=source_label,
                                                  tr=tr_DelCreate)
            Relvar.insert(db=mmdb, tr=tr_DelCreate, relvar='Initialization Source', tuples=[
                Initialization_Source_i(Source_flow=source_fid, Delegating_activity=self.delegating_anum,
                                        Creation_activity=self.anum, Local_flow=local_attr_flow.fid, Domain=self.domain)
            ])
            local_attr_flows[attr_name] = local_attr_flow.fid
            # TODO: If delegated flows are unlabled, we should label the local flows to match the attr names

        # Mirror any reference initialiation flows from the delegating activity
        rnum_refs = []
        for rel, refs in self.ref_inits.items():
            local_ref_flows = []
            for ref in refs:
                local_ref_flow = Flow.copy_data_flow(tr=tr_DelCreate, ref_fid=ref, ref_anum=self.delegating_anum,
                                                     new_anum=self.anum, domain=self.domain)
                local_ref_flows.append(local_ref_flow.fid)
                Relvar.insert(db=mmdb, tr=tr_DelCreate, relvar='Initialization Source', tuples=[
                    Initialization_Source_i(Source_flow=ref, Delegating_activity=self.delegating_anum,
                                            Creation_activity=self.anum, Local_flow=local_ref_flow.fid,
                                            Domain=self.domain)
                ])
            rnum_refs.append(Flow_refs(rnum=rel, ref_flow1=refs[0], ref_flow2=None if len(refs) != 2 else refs[1]))
        new_inst = New_delegated_inst(cname=self.class_name, attr_flows=local_attr_flows, ref_flows=rnum_refs)

        Transaction.execute(db=mmdb, name=tr_DelCreate)

        # Now populate the creation action
        ca = CreateAction(statement_parse=new_inst, activity=self.activity)
        b = ca.process()
        pass

