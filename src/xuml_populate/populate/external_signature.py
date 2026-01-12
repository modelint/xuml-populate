"""
external_signature.py – Populate an External Signature
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
from xuml_populate.populate.mmclass_nt import External_Signature_i, Parameter_i

if __debug__:
    from xuml_populate.utility import print_mmdb


_logger = logging.getLogger(__name__)

class ExternalSignature:
    """
    Populate an External Signature
    """

    @classmethod
    def populate(cls, tr: str, params: list[dict[str, str]], domain: str) -> str:
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
        for p in params:
            # TODO: Consider supporting table type output (not classes)
            # Populate the type if it is not already populated
            MMtype.populate_scalar(name=p['type'], domain=domain)
            # Populate the Parameter
            Relvar.insert(db=mmdb, tr=tr, relvar='Parameter', tuples=[
                Parameter_i(Name=p['name'], Signature=signum, Domain=domain, Type=p['type'])
            ])
        return signum
