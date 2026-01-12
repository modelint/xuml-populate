"""
external_event.py – Populate an External Operation
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
    External_Operation_i, External_Operation_Output_i, External_Service_i, External_Signature_i
)

if __debug__:
    from xuml_populate.utility import print_mmdb


_logger = logging.getLogger(__name__)

class ExternalOperation:
    """
    Create an operation relation
    """
    @classmethod
    def populate(cls, ee: str, domain: str, parse: dict[str, dict], ee_populated: bool):
        """
        Populate an External Operation

        Args:
            ee: Name of the EE
            domain: Name of the domain
            parse: Dictionary obtained from parse of external services file
            ee_populated: True if this service's EE has been populate
        """
        if ee_populated:
            # EE is already populated, so we start a new transaction for this service
            tr = 'External Operation'
            Transaction.open(db=mmdb, name=tr)
        else:
            # EE requires at least one service and it has not yet been populated, so we use the open EE transaction
            tr = EE.tr

            # Populate the External Operation
            op_name = parse["name"]
            Relvar.insert(db=mmdb, tr=tr, relvar='External Operation', tuples=[
                External_Operation_i(Name=op_name, EE=ee, Domain=domain)
            ])
            # Populate the External Signature
            op_params = parse.get('parameters', [])
            signum = ExternalSignature.populate(tr=tr, params=op_params, domain=domain)
            Relvar.insert(db=mmdb, tr=tr, relvar='External Service', tuples=[
                External_Service_i(Name=op_name, Signature=signum, Domain=domain, EE=ee)
            ])

            # If the operation returns a value, populate the External Operation Output
            rtype = parse.get('type')
            Relvar.insert(db=mmdb, tr=tr, relvar='External Operation Output', tuples=[
                External_Operation_Output_i(Operation=op_name, EE=ee, Domain=domain, Type=rtype)
            ])
            Transaction.execute(db=mmdb, name=tr)
