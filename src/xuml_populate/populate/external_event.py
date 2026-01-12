"""
external_event.py – Populate an External Event
"""

# System
import logging

# Model Integration
from pyral.transaction import Transaction
from pyral.relvar import Relvar

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.signature import Signature
from xuml_populate.populate.activity import Activity
from xuml_populate.populate.mm_type import MMtype
from xuml_populate.populate.ee import EE
from xuml_populate.populate.external_signature import ExternalSignature
from xuml_populate.populate.mmclass_nt import (
    External_Event_i, Service_Response_i, External_Service_i, External_Signal_Action_i,
    External_Signal_Parameter_i
)

if __debug__:
    from xuml_populate.utility import print_mmdb


_logger = logging.getLogger(__name__)

class ExternalEvent:
    """
    Populate an External Event
    """
    @classmethod
    def populate(cls, ee: str, domain: str, parse: dict[str, dict], ee_populated: bool):
        """
        Populate an External Event

        Args:
            ee: Name of the EE
            domain: Name of the domain
            parse: Event dictionary obtained from parse of external services file
            ee_populated: True if this service's EE has been populate
        """
        if ee_populated:
            # EE is already populated, so we start a new transaction for this service
            tr = 'External Event'
            Transaction.open(db=mmdb, name=tr)
        else:
            # EE requires at least one service and it has not yet been populated, so we use the open EE transaction
            tr = EE.tr

        # Populate External Event
        ev_name = parse["name"]
        Relvar.insert(db=mmdb, tr=tr, relvar='External Event', tuples=[
            External_Event_i(Name=ev_name, Domain=domain)
        ])

        # Populate the External Signature
        event_params = parse.get('parameters', [])
        signum = ExternalSignature.populate(tr=tr, params=event_params, domain=domain)
        Relvar.insert(db=mmdb, tr=tr, relvar='External Service', tuples=[
            External_Service_i(Name=ev_name, Signature=signum, Domain=domain, EE=ee)
        ])

        # Populate all Service Responses
        responses = parse.get('responses', [])
        for r in responses:
            Relvar.insert(db=mmdb, tr=tr, relvar='Service Response', tuples=[
                Service_Response_i(External_event=ev_name, Response_event=r["name"], State_model=r["state model"],
                                   Domain=domain)
            ])

        Transaction.execute(db=mmdb, name=tr)
