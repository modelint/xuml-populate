"""
delete_statement.py – Unpack a delete statement into one or more delete actions
"""
# System
import logging

# Model Integration
from scrall.parse.visitor import Delete_Group_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
from xuml_populate.utility import print_mmdb
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.delete_action import DeleteAction
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.actions.aparse_types import ActivityAP, Boundary_Actions

_logger = logging.getLogger(__name__)

class DeleteStatement:
    """
    Populate all components of a call statement

    This can be a method call, an ee operation, or the invocation of a type operation.

    The first component is either an Instance Set (INST_a) or just a name (N_a)

    If it is just a name, that name must be the name of a

    """

    def __init__(self, statement_parse: Delete_Group_a, activity_data: ActivityAP):
        """

        Args:
            statement_parse: A parsed deletion group
            activity_data:
        """
        self.parse = statement_parse
        self.activity_data = activity_data

    def process(self) -> Boundary_Actions:
        """

        Returns:

        """
        input_actions: set[str] = set()
        output_actions: set[str] = set()
        for iset_parse in self.parse.instance_sets:
            delete_a = DeleteAction(iset_parse=iset_parse, activity_data=self.activity_data)
            boundary_actions = delete_a.process()
            input_actions.update(boundary_actions.ain)
            output_actions.update(boundary_actions.aout)

        return Boundary_Actions(ain=input_actions, aout=output_actions)