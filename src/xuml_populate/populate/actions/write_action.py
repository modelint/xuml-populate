"""
write_action.py – Populate a write action instance in PyRAL
"""
# System
import logging
from typing import Set, List, Tuple, TYPE_CHECKING

# Model Integration
from pyral.relvar import Relvar
from pyral.transaction import Transaction

# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, ActivityAP
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.mm_class import MMclass
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Write_Action_i, Attribute_Write_Access_i

_logger = logging.getLogger(__name__)

# Transactions
tr_Write = "Write Action"

class WriteAction:
    """
    Create all relations for a Write Action
    """

    def __init__(self, write_to_instance_flow: Flow_ap, value_to_write_flow: Flow_ap, attr_name: str,
                 activity:'Activity'):
        """

        Args:
            write_to_instance_flow: Update an attribute value of this instance
            value_to_write_flow: Input scalar flow (the value to be written)
            attr_name: The attribute name
            activity: The enclosing Activity
        """
        assert write_to_instance_flow.content == Content.INSTANCE
        assert write_to_instance_flow.max_mult == MaxMult.ONE
        self.write_to_instance_flow = write_to_instance_flow  # We are selecting instances from this instance flow
        self.cname = write_to_instance_flow.tname
        self.anum = activity.anum
        self.domain = activity.domain
        self.attr_name = attr_name
        self.value_to_write_flow = value_to_write_flow

        self.output_instance_flow = None
        self.action_id = None

    def populate(self) -> str:
        """
        Populate the Write Action

        Returns:
            action_id
        """
        # Populate the Action superclass instance and obtain its action_id
        Transaction.open(db=mmdb, name=tr_Write)
        self.action_id = Action.populate(tr=tr_Write, anum=self.anum, domain=self.domain, action_type="write")
        Relvar.insert(db=mmdb, tr=tr_Write, relvar='Write Action', tuples=[
            Write_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                           Instance_flow=self.write_to_instance_flow.fid)
        ])

        Relvar.insert(db=mmdb, tr=tr_Write, relvar='Attribute Write Access', tuples=[
            Attribute_Write_Access_i(Attribute=self.attr_name, Class=self.cname, Write_action=self.action_id,
                                     Activity=self.anum, Domain=self.domain, Input_flow=self.value_to_write_flow.fid)
        ])

        # We now have a transaction with all select-action instances, enter into the metamodel db
        Transaction.execute(db=mmdb, name=tr_Write)  # write action
        return self.action_id
