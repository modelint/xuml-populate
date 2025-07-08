"""
write_action.py – Populate a write action instance in PyRAL
"""
# System
import logging
from typing import Set, List, Tuple

# Model Integration
from pyral.relvar import Relvar
from pyral.transaction import Transaction

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.mm_class import MMclass
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Write_Action_i, Attribute_Write_Access_i

_logger = logging.getLogger(__name__)

# Transactions
tr_write = "Write Action"

class WriteAction:
    """
    Create all relations for a Write Action
    """

    input_instance_flow = None  # We are selecting instances from this instance flow
    output_instance_flow = None
    action_id = None

    @classmethod
    def populate(cls, input_single_instance_flow: Flow_ap, input_sflow: Flow_ap, attr_name: str,
                 anum: str, domain: str) -> str:
        """
        Populate the Write Action

        :param input_single_instance_flow: Update an attribute value of this instance
        :param attr_name: The attribute name
        :param input_sflow: Input scalar flow (the value to be written)
        :param anum:  The activity number
        :param domain:  The domain name
        :return: action_id
        """

        assert input_single_instance_flow.content == Content.INSTANCE
        assert input_single_instance_flow.max_mult == MaxMult.ONE
        cname = input_single_instance_flow.tname

        # Get the class header
        class_attrs = MMclass.header(cname=cname, domain=domain)

        # Populate the Action superclass instance and obtain its action_id
        Transaction.open(db=mmdb, name=tr_write)
        action_id = Action.populate(tr=tr_write, anum=anum, domain=domain, action_type="write")  # Transaction open
        Relvar.insert(db=mmdb, tr=tr_write, relvar='Write Action', tuples=[
            Write_Action_i(ID=action_id, Activity=anum, Domain=domain, Instance_flow=input_single_instance_flow.fid)
        ])

        Relvar.insert(db=mmdb, tr=tr_write, relvar='Attribute Write Access', tuples=[
            Attribute_Write_Access_i(Attribute=attr_name, Class=cname, Write_action=action_id, Activity=anum,
                                     Domain=domain, Input_flow=input_sflow.fid)
        ])

        # We now have a transaction with all select-action instances, enter into the metamodel db
        Transaction.execute(db=mmdb, name=tr_write)  # write action
        return action_id
