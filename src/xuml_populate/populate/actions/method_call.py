"""
method_call.py – Process a call action
"""
# System
import logging

# Model Integration
from scrall.parse.visitor import Call_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.actions.aparse_types import ActivityAP, Boundary_Actions

class MethodCall:
    """
    Populate all components of a Method Call action and any other
    actions required by the parse
    """

    def __init__(self, method_name: str, method_class: str, parse: Call_a,
                 activity_data: ActivityAP) -> Boundary_Actions:
        """

        Args:
            call_parse:
            activity_data:
        """
        self.method_name = method_name
        self.method_calss = method_class
        self.parse = parse
        self.activity_data = activity_data

    def process(self):
        """

        Returns:

        """
        pass

