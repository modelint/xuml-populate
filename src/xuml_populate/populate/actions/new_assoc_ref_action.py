"""
new_assoc_ref_action.py – Populate a New Associative Reference Action
"""

# System
import logging
from typing import List, TYPE_CHECKING

# Model Integration
from scrall.parse.visitor import To_ref_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.utility import print_mmdb
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

class NewAssociativeReferenceAction:
    """

    """
    @classmethod
    def from_delegated(cls, tr: str, create_action_id: str, new_inst: New_delegated_inst, activity: 'Activity'):
        pass

    @classmethod
    def from_local(cls, tr: str, create_action_id: str, action_parse: To_ref_a, activity: 'Activity'):
        pass

    def __init__(self, tr: str, create_action_id: str, new_inst: To_ref_a | New_delegated_inst,
                 activity: 'Activity'):
        """

        """
        self.tr = tr
        self.create_action_id = create_action_id
        if type(new_inst).__name__ == 'New_delegated_inst':
            self.new_delegated_inst = new_inst
            self.new_inst = False
        else:
            self.new_inst



        self.p_class = None
        self.t_class = None
        self.ref_flows: dict[str, str] = {}
        self.parse = new_inst
        self.activity = activity
        self.domain = activity.domain
        self.anum = activity.anum
        self.rnum = new_inst.rnum.rnum
        self.action_id = None

    def populate(self) -> tuple[str, list[str]]:
        """

        Returns:
            Flow ID of a tuple of referential attribute values
        """
        self.action_id = Action.populate(tr=self.tr, anum=self.anum, domain=self.domain,
                                         action_type="new assoc ref")
        Relvar.insert(db=mmdb, tr=self.tr, relvar="New Reference Action", tuples=[
            New_Reference_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                                   Create_action=self.create_action_id)
        ])

        # Now we need to create the t and p class names
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
        ], tr=self.tr)
        Relvar.insert(db=mmdb, relvar="Referenced Instance", tuples=[
            Referenced_Instance_i(Flow=self.ref_flows[self.t_class], Activity=self.anum, Domain=self.domain)
        ], tr=self.tr)
        Relvar.insert(db=mmdb, relvar="P Ref Instance", tuples=[
            P_Ref_Instance_i(Flow=self.ref_flows[self.p_class], Activity=self.anum, Domain=self.domain)
        ], tr=self.tr)
        Relvar.insert(db=mmdb, relvar="Referenced Instance", tuples=[
            Referenced_Instance_i(Flow=self.ref_flows[self.p_class], Activity=self.anum, Domain=self.domain)
        ], tr=self.tr)

        Relvar.insert(db=mmdb, relvar="New Associative Reference Action", tuples=[
            New_Associative_Reference_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                                               T_instance=self.ref_flows[self.t_class],
                                               P_instance=self.ref_flows[self.p_class])
        ], tr=self.tr)
        print_mmdb()

        # Create the output tuple table type
        # Get all referential attributes associated with the associatie relationship
        R = f"Rnum:<{self.rnum}>, Domain:<{self.domain}>"
        aref_r = Relation.restrict(db=mmdb, relation='Attribute Reference', restriction=R, svar_name="arefs")
        p_r = Relation.project(db=mmdb, attributes=("From_attribute", "From_class", "Domain"))
        a_r = Relation.semijoin(db=mmdb, rname2="Attribute", attrs={"From_attribute": "Name", "From_class": "Class",
                                                                    "Domain": "Domain"})
        name_type_pairs = {t["Name"]: t["Scalar"] for t in a_r.body}
        # tname = Table.populate(tr=self.tr, table_header=name_type_pairs, domain=self.domain)

        # Now create the tuple flow
        tflow_label = f"_{self.rnum}_ref_{self.create_action_id[4:]}"
        tf = Flow.populate_relation_flow_by_header(
            table_header=name_type_pairs, anum=self.anum, domain=self.domain, max_mult=MaxMult.ONE,
            label=tflow_label)

        Relvar.insert(db=mmdb, tr=self.tr, relvar="Instance Action", tuples=[
            Instance_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=self.tr, relvar="Reference Action", tuples=[
            Reference_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                               Association=self.parse.rnum.rnum, Ref_attr_values=tf.fid)
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
                R = f"Name:<{iset.name}>, Activity:<{self.anum}>, Domain:<{self.domain}>"
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
