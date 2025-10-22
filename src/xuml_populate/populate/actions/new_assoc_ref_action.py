"""
new_assoc_ref_action.py – Populate a New Associative Reference Action
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
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.table import Table
from xuml_populate.populate.actions.aparse_types import Flow_ap, Content, MaxMult, New_delegated_inst
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.mmclass_nt import (New_Associative_Reference_Action_i, Reference_Action_i,
                                               New_Reference_Action_i, T_Ref_Instance_i, P_Ref_Instance_i,
                                               Referenced_Instance_i, Instance_Action_i)
_logger = logging.getLogger(__name__)

if __debug__:
    from xuml_populate.utility import print_mmdb

class NewAssociativeReferenceAction:
    """

    """
    @classmethod
    def from_delegated(cls, tr: str, create_action_id: str, rnum: str, ref_fid1: str, ref_fid2: str,
                       activity: 'Activity'):
        return cls(tr=tr, create_action_id=create_action_id, rnum=rnum, ref1=ref_fid1, ref2=ref_fid2,
                   is_delegated=True, activity=activity)

    @classmethod
    def from_local(cls, tr: str, create_action_id: str, rnum: str, ref1, ref2, activity: 'Activity'):
        return cls(tr=tr, create_action_id=create_action_id, rnum=rnum, ref1=ref1, ref2=ref2, is_delegated=False,
                   activity=activity)

    def __init__(self, tr: str, create_action_id: str, rnum: str, ref1, ref2, is_delegated: bool, activity: 'Activity'):
        """
        """
        self.tr = tr
        self.create_action_id = create_action_id
        self.is_delegated = is_delegated
        self.rnum = rnum
        self.ref1 = ref1
        self.ref2 = ref2
        self.activity = activity

        self.p_class = None
        self.t_class = None
        self.ref_flows: dict[str, str] = {}
        self.action_id = None

    def populate(self) -> tuple[str, list[str]]:
        """

        Returns:
            Flow ID of a tuple of referential attribute values
        """
        self.action_id = Action.populate(tr=self.tr, anum=self.activity.anum, domain=self.activity.domain,
                                         action_type="new assoc ref")

        # Now we need to create the t and p class names
        R = f"Ref_type:<T>, Rnum:<{self.rnum}>, Domain:<{self.activity.domain}>"
        tref_r = Relation.restrict(db=mmdb, relation='Association Reference', restriction=R)
        R = f"Ref_type:<P>, Rnum:<{self.rnum}>, Domain:<{self.activity.domain}>"
        pref_r = Relation.restrict(db=mmdb, relation='Association Reference', restriction=R)

        self.t_class = tref_r.body[0]["To_class"]
        self.p_class = pref_r.body[0]["To_class"]

        # Obtain the T and P instance flows typed by the participating Classes
        if not self.is_delegated:
            self.get_iflow(iset=self.ref1)
            self.get_iflow(iset=self.ref2)
        else:
            ref1_flow = Flow.lookup_data(fid=self.ref1, anum=self.activity.anum, domain=self.activity.domain)
            ref2_flow = Flow.lookup_data(fid=self.ref2, anum=self.activity.anum, domain=self.activity.domain)
            self.ref_flows[ref1_flow.tname] = self.ref1
            self.ref_flows[ref2_flow.tname] = self.ref2
            pass

        # Populate links to the source Single Instance Flows
        Relvar.insert(db=mmdb, relvar="T Ref Instance", tuples=[
            T_Ref_Instance_i(Flow=self.ref_flows[self.t_class], Activity=self.activity.anum,
                             Domain=self.activity.domain) ], tr=self.tr)
        Relvar.insert(db=mmdb, relvar="Referenced Instance", tuples=[
            Referenced_Instance_i(Flow=self.ref_flows[self.t_class], Activity=self.activity.anum,
                                  Domain=self.activity.domain)], tr=self.tr)
        Relvar.insert(db=mmdb, relvar="P Ref Instance", tuples=[
            P_Ref_Instance_i(Flow=self.ref_flows[self.p_class], Activity=self.activity.anum,
                             Domain=self.activity.domain)], tr=self.tr)
        Relvar.insert(db=mmdb, relvar="Referenced Instance", tuples=[
            Referenced_Instance_i(Flow=self.ref_flows[self.p_class], Activity=self.activity.anum,
                                  Domain=self.activity.domain)], tr=self.tr)

        Relvar.insert(db=mmdb, relvar="New Associative Reference Action", tuples=[
            New_Associative_Reference_Action_i(ID=self.action_id, Activity=self.activity.anum,
                                               Domain=self.activity.domain,
                                               T_instance=self.ref_flows[self.t_class],
                                               P_instance=self.ref_flows[self.p_class])], tr=self.tr)

        # Create the output tuple table type
        # Get all referential attributes associated with the associative relationship
        R = f"Rnum:<{self.rnum}>, Domain:<{self.activity.domain}>"
        aref_r = Relation.restrict(db=mmdb, relation='Attribute Reference', restriction=R, svar_name="arefs")
        p_r = Relation.project(db=mmdb, attributes=("From_attribute", "From_class", "Domain"))
        a_r = Relation.semijoin(db=mmdb, rname2="Attribute", attrs={"From_attribute": "Name", "From_class": "Class",
                                                                    "Domain": "Domain"})
        name_type_pairs = {t["Name"]: t["Scalar"] for t in a_r.body}
        # tname = Table.populate(tr=self.tr, table_header=name_type_pairs, domain=self.domain)

        # Now create the tuple flow
        tflow_label = f"_{self.rnum}_ref_{self.create_action_id[4:]}"
        tf = Flow.populate_relation_flow_by_header(
            table_header=name_type_pairs, anum=self.activity.anum, domain=self.activity.domain,
            max_mult=MaxMult.ONE, label=tflow_label
        )
        Relvar.insert(db=mmdb, tr=self.tr, relvar="Instance Action", tuples=[
            Instance_Action_i(ID=self.action_id, Activity=self.activity.anum,
                              Domain=self.activity.domain)])
        Relvar.insert(db=mmdb, tr=self.tr, relvar="Reference Action", tuples=[
            Reference_Action_i(ID=self.action_id, Activity=self.activity.anum, Domain=self.activity.domain,
                               Association=self.rnum)])
        Relvar.insert(db=mmdb, tr=self.tr, relvar="New Reference Action", tuples=[
            New_Reference_Action_i(ID=self.action_id, Activity=self.activity.anum, Domain=self.activity.domain,
                                   Create_action=self.create_action_id, Ref_attr_values=tf.fid)
        ])

        ref_attr_names = [k for k in name_type_pairs.keys()]

        return tf.fid, ref_attr_names

    def get_iflow(self, iset):
        """

        Args:
            iset:

        """
        flow_id = None
        iset_type = type(iset).__name__
        match iset_type:
            case 'N_a' | 'IN_a':
                # It's just a single name, so we don't need to create an InstanceSet
                # since we know there won't be any new Actions or flows populated
                # We just need to find the named flow
                R = f"Name:<{iset.name}>, Activity:<{self.activity.anum}>, Domain:<{self.activity.domain}>"
                labeled_flow_r = Relation.restrict(db=mmdb, relation='Labeled Flow', restriction=R)
                if len(labeled_flow_r.body) == 1:
                    flow_id = labeled_flow_r.body[0]['ID']
                    iflow_r = Relation.semijoin(db=mmdb, rname2="Instance Flow")
                    flow_class = iflow_r.body[0]["Class"]
                    self.ref_flows[flow_class] = flow_id
                return
            case 'INST_a':
                from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
                pop_iset = InstanceSet(input_instance_flow=self.activity.xiflow, iset_components=iset.components,
                                       activity=self.activity)
                ain, aout, f = pop_iset.process()
                self.ref_flows[f.tname] = f.fid
                return
            case _:
                pass
