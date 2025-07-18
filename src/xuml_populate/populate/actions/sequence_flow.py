"""
sequence_flow.py – Populate a sequence control flow dependency
"""

# System
import logging

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Sequence_Flow_i

_logger = logging.getLogger(__name__)

# Transactions
tr_Seq = "SequenceFlow"

class SequenceFlow:
    """
    Create all relations for a Sequence Flow
    """

    def __init__(self, token: str, source_aid: str, dest_aids: set[str], anum: str, domain: str):
        self.token = token
        self.source_aid = source_aid
        self.dest_aids = dest_aids
        self.anum = anum
        self.domain = domain

        self.populate()

    def populate(self):
        """
        Populate a Sequence Flow
        """
        Transaction.open(db=mmdb, name=tr_Seq)
        # Populate the control flow
        fid = Flow.populate_control_flow(tr=tr_Seq, enabled_actions=self.dest_aids,
                                         anum=self.anum, domain=self.domain, label=self.token)
        Relvar.insert(db=mmdb, relvar="Sequence Flow", tuples=[
            Sequence_Flow_i(Source_action=self.source_aid, Flow=fid, Activity=self.anum, Domain=self.domain)
        ], tr=tr_Seq)
        # Not populating Emitter or Emitter Input since these are probably replaced by Gate
        Transaction.execute(db=mmdb, name=tr_Seq)

