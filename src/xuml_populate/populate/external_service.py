"""
external_service.py – Populate external services from parsed input
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
from xuml_populate.populate.mmclass_nt import (External_Operation_i, External_Operation_Output_i, External_Service_i,
                                               External_Event_i, External_Signature_i, Parameter_i)

if __debug__:
    from xuml_populate.utility import print_mmdb


_logger = logging.getLogger(__name__)

tr_ExternalOperation = "External_Operation"
tr_ExternalEvent = "External_Event"

class ExternalService:
    """
    Create a operation relation
    """
    @classmethod
    def populate_all(cls, domain: str, parse: dict[str, dict]):
        """
        For each class in the parse, populate any delegated External Services

        Args:
            domain: Name of the domain
            parse: Dictionary obtained from parse of external services file
        """
        for class_name, services in parse.items():

            # Populate all external operations for this class, if any
            ops_parse = services.get('external operations')
            if ops_parse is not None:
                for op in ops_parse:
                    Transaction.open(db=mmdb, name=tr_ExternalOperation)
                    # Populate the External Operation
                    Relvar.insert(db=mmdb, tr=tr_ExternalOperation, relvar='External Operation', tuples=[
                        External_Operation_i(Name=op["name"], Domain=domain)
                    ])
                    # Populate the External Signature
                    signum = cls.populate_sig(tr=tr_ExternalOperation, params=op['parameters'], domain=domain)
                    Relvar.insert(db=mmdb, tr=tr_ExternalOperation, relvar='External Service', tuples=[
                        External_Service_i(Name=op["name"], Signature=signum, Domain=domain, Class=class_name)
                    ])

                    # If the operation returns a value, populate the External Operation Output
                    rtype = op.get('return')
                    if rtype is not None:
                        Relvar.insert(db=mmdb, tr=tr_ExternalOperation, relvar='External Operation Output', tuples=[
                            External_Operation_Output_i(Operation=op["name"], Domain=domain, Type=rtype)
                        ])
                    Transaction.execute(db=mmdb, name=tr_ExternalOperation)

            # Populate all external events for this class, if any
            event_parse = services.get('external events')
            if event_parse is not None:
                Transaction.open(db=mmdb, name=tr_ExternalEvent)
                # Populate External Event
                Relvar.insert(db=mmdb, tr=tr_ExternalEvent, relvar='External Event', tuples=[
                    External_Event_i(Name=op["name"], Domain=domain)
                ])
                # Populate the External Signature
                signum = cls.populate_sig(tr=tr_ExternalEvent, params=op['parameters'], domain=domain)
                Relvar.insert(db=mmdb, tr=tr_ExternalEvent, relvar='External Service', tuples=[
                    External_Service_i(Name=op["name"], Signature=signum, Domain=domain, Class=class_name)
                ])
                Transaction.execute(db=mmdb, name=tr_ExternalEvent)

    @classmethod
    def populate_sig(cls, tr: str, params: dict[str, str], domain: str) -> str:
        """
        Populate an External Signature instance in the current traansaction

        Args:
            tr: The current transaction name (op/event)
            params: A dictionary of parameter name : type name pairs
            domain: The domain name

        Returns:
            The assigned signature number
        """
        signum = Signature.populate(tr=tr, domain=domain)
        Relvar.insert(db=mmdb, tr=tr, relvar='External Signature', tuples=[
            External_Signature_i(SIGnum=signum, Domain=domain)
        ])
        for n, t in params.items():
            # TODO: Consider supporting table type output (not classes)
            # Populate the type if it is not already populated
            MMtype.populate_scalar(name=t, domain=domain)
            # Populate the Parameter
            Relvar.insert(db=mmdb, tr=tr, relvar='Parameter', tuples=[
                Parameter_i(Name=n, Signature=signum, Domain=domain, Type=t)
            ])
        return signum
