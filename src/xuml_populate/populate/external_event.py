"""
external_event.py – Populate an External Event
"""

# System
import logging

# Model Integration
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from pyral.relation import Relation

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
    implicit_state_entry = {}

    @classmethod
    def populate_implicit_state_entry_ext_event(cls, ees: list[str], state_name: str, class_name: str, domain: str,
                                                unpopulated_ees: dict[str, str]):
        """
        Populate implicit state entry external events

        Args:
            ees: One or more implicit ext event target EEs
            state_name: Name of the state to be entered
            class_name: State of this class (state must be in a lifecycle state model)
            domain: Defined in this domain
            unpopulated_ees:  Any ees that were defined in the external yaml, but not populated yet
        """
        # Verify that each EE is populated
        for ee in ees:
            pass
            # Generate an event name based on the state name
            # Generate the event specification
            if ee in unpopulated_ees:
                # Open a new EE transaction and insert the EE instance
                EE.populate(name=ee, domain=domain, service_domain=unpopulated_ees[ee])
                tr = EE.tr
                del unpopulated_ees[ee]  # It will no longer be unpopulated
            else:
                # EE is already populated, so we start a new transaction for this service
                tr = 'External Event'
                Transaction.open(db=mmdb, name=tr)

            # To make the generated event names look reasonable, we start with the class name in title case
            # as it normally is, and then drop the state name to an initial cap on the first word
            # Door opening or Accessible Shaft Level clear stop request, for example
            event_name = f"{class_name} {state_name.lower()}"

            # Associate the lifecycle state with the implicit event so that we can
            # look for it when populating the state activity
            cls.implicit_state_entry.setdefault(class_name, {})[state_name] = event_name

            cls.populate(ee=ee, domain=domain, ev_name=event_name, params={}, responses=[], tr=tr)
        pass

    @classmethod
    def populate(cls, ee: str, domain: str, ev_name: str, params: dict[str, str],
                 responses: list[dict[str, str]], tr: str):
        pass
        # Populate External Event
        Relvar.insert(db=mmdb, tr=tr, relvar='External Event', tuples=[
            External_Event_i(Name=ev_name, EE=ee, Domain=domain)
        ])

        # Populate the External Signature
        signum = ExternalSignature.populate(tr=tr, params=params, domain=domain)
        Relvar.insert(db=mmdb, tr=tr, relvar='External Service', tuples=[
            External_Service_i(Name=ev_name, Signature=signum, Domain=domain, EE=ee)
        ])

        # Populate all Service Responses
        for r in responses:
            Relvar.insert(db=mmdb, tr=tr, relvar='Service Response', tuples=[
                Service_Response_i(External_event=ev_name, Response_event=r["name"], State_model=r["state model"],
                                   EE=ee, Domain=domain)
            ])

        Transaction.execute(db=mmdb, name=tr)

    @classmethod
    def populate_explicit(cls, ee: str, domain: str, ev_name: str, params: dict[str, str],
                          responses: list[dict[str, str]], ee_tr: str | None):
        """
        Populate an External Event

        Args:
            ee: Name of the EE
            domain: Name of the domain
            ev_name: name of the external event
            params: dictionary of parameter / type names
            responses: Optional list of class / event spec names
            ee_tr: Open EE transaction if we are populating previously undefined EE
        """
        if not ee_tr:
            # EE is already populated, so we start a new transaction for this service
            tr = 'External Event'
            Transaction.open(db=mmdb, name=tr)
        else:
            # We are populating the EE as well, so just use its already open tr
            tr = ee_tr

        cls.populate(ee=ee, ev_name=ev_name, params=params, responses=responses, domain=domain, tr=tr)