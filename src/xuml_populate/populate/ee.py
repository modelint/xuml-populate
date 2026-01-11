"""
ee.py – Populate an External Entity
"""
# System
import logging

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.mmclass_nt import External_Entity_i

# Model Integration
from pyral.relvar import Relvar
from pyral.transaction import Transaction

_logger = logging.getLogger(__name__)


class EE:
    """
    Populate an External Entity
    """
    tr = 'External Entity'

    @classmethod
    def populate(cls, name: str, domain: str):
        # Open a transaction for this EE and insert the EE instance
        Transaction.open(db=mmdb, name=cls.tr)
        Relvar.insert(db=mmdb, relvar='External Entity', tuples=[
            External_Entity_i(Name=name, Domain=domain)
        ])