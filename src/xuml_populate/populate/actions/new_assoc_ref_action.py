"""
new_assoc_ref_action.py – Populate a New Associative Reference Action
"""

# System
import logging
from typing import List

# Model Integration
from scrall.parse.visitor import To_ref_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
from xuml_populate.utility import print_mmdb
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, ActivityAP, Content
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.mmclass_nt import (New_Associative_Reference_Action_i, Reference_Action_i,
                                               New_Reference_Action_i, T_Ref_Instance_i, P_Ref_Instance_i,
                                               Referenced_Instance_i)
_logger = logging.getLogger(__name__)

# Transactions
tr_AssocRef = "New Assoc Ref Action"


class NewAssociativeReferenceAction:
    """

    """

    def __init__(self, create_action_id: str, action_parse: To_ref_a, activity_data: ActivityAP):
        """

        """
        self.create_action_id = create_action_id
        self.p_class = None
        self.t_class = None
        self.ref_flows: dict[str, str] = {}
        self.parse = action_parse
        self.activity_data = activity_data
        self.domain = activity_data.domain
        self.anum = activity_data.anum
        self.rnum = action_parse.rnum.rnum
        self.action_id = None
        pass

    def populate(self) -> str:
        """

        Returns:
            Flow ID of a tuple of referential attribute values
        """
        Transaction.open(db=mmdb, name=tr_AssocRef)
        self.action_id = Action.populate(tr=tr_AssocRef, anum=self.anum, domain=self.domain,
                                         action_type="new assoc ref")
        Relvar.insert(db=mmdb, relvar="Reference Action", tuples=[
            Reference_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain, Association=self.parse.rnum.rnum)
        ], tr=tr_AssocRef)
        Relvar.insert(db=mmdb, relvar="New Reference Action", tuples=[
            New_Reference_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                                   Create_action=self.create_action_id)
        ], tr=tr_AssocRef)

        # Nowe we need to create the t and p class names
        R = f"Ref_type:<T>, Rnum:<{self.rnum}>, Domain:<{self.domain}>"
        tref_r = Relation.restrict(db=mmdb, relation='Association Reference', restriction=R)
        R = f"Ref_type:<P>, Rnum:<{self.rnum}>, Domain:<{self.domain}>"
        pref_r = Relation.restrict(db=mmdb, relation='Association Reference', restriction=R)

        self.t_class = tref_r.body[0]["To_class"]
        self.p_class = pref_r.body[0]["To_class"]

        # Obtain the T and P instance flows typed by the participating Classes
        self.get_iflow(iset=self.parse.iset1)
        self.get_iflow(iset=self.parse.iset2)

        # Populate links to the source Single Instance Flows
        Relvar.insert(db=mmdb, relvar="T Ref Instance", tuples=[
            T_Ref_Instance_i(Flow=self.ref_flows[self.t_class], Activity=self.anum, Domain=self.domain)
        ], tr=tr_AssocRef)
        Relvar.insert(db=mmdb, relvar="Referenced Instance", tuples=[
            Referenced_Instance_i(Flow=self.ref_flows[self.t_class], Activity=self.anum, Domain=self.domain)
        ], tr=tr_AssocRef)
        Relvar.insert(db=mmdb, relvar="P Ref Instance", tuples=[
            P_Ref_Instance_i(Flow=self.ref_flows[self.p_class], Activity=self.anum, Domain=self.domain)
        ], tr=tr_AssocRef)
        Relvar.insert(db=mmdb, relvar="Referenced Instance", tuples=[
            Referenced_Instance_i(Flow=self.ref_flows[self.p_class], Activity=self.anum, Domain=self.domain)
        ], tr=tr_AssocRef)

        Transaction.execute(db=mmdb, name=tr_AssocRef)

        pass

    def get_iflow(self, iset):

        flow_id = None
        iset_type = type(iset).__name__
        match iset_type:
            case 'N_a' | 'IN_a':
                # It's just a single name, so we don't need to create an InstanceSet
                # since we know there won't be any new Actions or flows populated
                # We just need to find the named flow
                R = f"Name:<{iset.name}>, Activity:<{self.anum}>, Domain:<{self.domain}>"
                labeled_flow_r = Relation.restrict(db=mmdb, relation='Labeled Flow', restriction=R)
                if len(labeled_flow_r.body) == 1:
                    flow_id = labeled_flow_r.body[0]['ID']
                    iflow_r = Relation.semijoin(db=mmdb, rname2="Instance Flow")
                    flow_class = iflow_r.body[0]["Class"]
                    self.ref_flows[flow_class] = flow_id
                return
            case 'INST_a':
                pop_iset = InstanceSet(input_instance_flow=self.activity_data.xiflow, iset_components=iset.components,
                                       activity_data=self.activity_data)
                ain, aout, f = pop_iset.process()
                self.ref_flows[f.tname] = f.fid
                return
            case _:
                pass

        pass