"""
iterator.py – Populate an Iterator action superclass
"""

# System
import logging
from typing import Sequence, TYPE_CHECKING, Optional

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction
from scrall.parse.visitor import BOOL_a, MATH_a, IN_a, N_a


# xUML populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import (Instance_Action_i, Iterator_i, Iterated_Instance_Flow_i)

if __debug__:
    from xuml_populate.utility import print_mmdb

_logger = logging.getLogger(__name__)


class IteratorAction:
    """
    Populate an Iterator
    """

    @classmethod
    def populate(cls, tr: str, input_mult_inst_flow: Flow_ap, activity: 'Activity') -> tuple[str, Flow_ap]:
        """
        Populate an Iterator superclass so that an Iterated Instance Flow can be obtained

        Args:
            tr: Enveloping transaction name
            input_mult_inst_flow: Multiple instance flow summary
            activity: The enclosing Activity

        Returns:
            An Iterated Instance Flow
        """
        # Create a Single instance flow with the same type, but single multiplicity
        # We can create the flow itself outside of the envelope transaction (in its own transaction)
        siflow = Flow.populate_instance_flow(cname=input_mult_inst_flow.content.name, anum=activity.anum,
                                             domain=activity.domain, single=True)
        # Now create the Iterated Instance Flow as part of the supplied envelope transaction
        Transaction.open(db=mmdb, name=tr)
        # Obtain an action id
        iterator_id = Action.populate(tr=tr, anum=activity.anum, domain=activity.domain, action_type="iterator")
        Relvar.insert(db=mmdb, tr=tr, relvar='Instance Action', tuples=[
            Instance_Action_i(ID=iterator_id, Activity=activity.anum, Domain=activity.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr, relvar='Iterator', tuples=[
            Iterator_i(ID=iterator_id, Activity=activity.anum, Domain=activity.domain,
                       Input_flow=input_mult_inst_flow.fid)
        ])
        Relvar.insert(db=mmdb, tr=tr, relvar='Iterated Instance Flow', tuples=[
            Iterated_Instance_Flow_i(Iterator=iterator_id, Activity=activity.anum, Domain=activity.domain,
                                     Flow=siflow.fid)
        ])

        return iterator_id, siflow
