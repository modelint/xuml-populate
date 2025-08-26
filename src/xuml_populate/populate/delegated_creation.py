""" delegated_creation.py -- Populate a Delegated Creation Activity """

# System
import logging
from typing import TYPE_CHECKING

# Model Integration
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from pyral.relation import Relation

# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.populate.mmclass_nt import Delegated_Create_Action_i
from xuml_populate.populate.actions.create_action import CreateAction
from xuml_populate.populate.actions.new_assoc_ref_action import NewAssociativeReferenceAction

class DelegatedCreationActivity:
    """

    """

    def __init__(self, scalar_init_flows, ref_init_flows, activity: 'Activity'):
        """

        """
        pass

    def populate(self):
        """

        Returns:
        """
        pass