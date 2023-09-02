"""
read_action.py – Populate a read action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.mm_class import MMclass
from scrall.parse.visitor import Projection_a
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Read_Action_i, Attribute_Read_Access_i
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class ReadAction:
    """
    Create all relations for a Read Action
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
    activity_path = None
    scrall_text = None
    max_mult = None


    @classmethod
    def populate(cls, mmdb: 'Tk', input_single_instance_flow: Flow_ap, projection: Projection_a, anum: str,
                 domain: str, activity_path: str, scrall_text: str) -> Dict[str, Flow_ap]:
        """
        Populate the Read Action

        :param mmdb:
        :param input_single_instance_flow: The source flow into this selection
        :param projection:
        :param input_single_instance_flow:
        :param anum:
        :param domain:
        :param select_agroup:  The parsed Scrall select action group
        :param scrall_text:
        :param activity_path:
        """
        si_flow = input_single_instance_flow  # Short name for convenience

        # Get the class header
        class_attrs = MMclass.header(mmdb, cname=si_flow.tname, domain=domain)

        # Populate the Action superclass instance and obtain its action_id
        action_id = Action.populate(mmdb, anum, domain)  # Transaction open
        Relvar.insert(relvar='Read_Action', tuples=[
            Read_Action_i(ID=action_id, Activity=anum, Domain=domain, Instance_flow=input_single_instance_flow.fid)
        ])
        output_flows = {}
        proj_attrs = [n.name for n in projection.attrs] if projection.expand != 'ALL' else list(class_attrs.keys())
        for pa in proj_attrs:
            of = Flow.populate_scalar_flow(mmdb, scalar_type=class_attrs[pa], activity=anum, domain=domain, label=None)
            Relvar.insert(relvar='Attribute_Read_Access', tuples=[
                Attribute_Read_Access_i(Attribute=pa, Class=si_flow.tname, Read_action=action_id, Activity=anum,
                                        Domain=domain, Output_flow=of.fid)
            ])
            output_flows[pa] = of
        # We now have a transaction with all select-action instances, enter into the metamodel db
        Transaction.execute()  # Select Action
        return output_flows
