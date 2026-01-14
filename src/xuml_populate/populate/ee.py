"""
ee.py – Populate an External Entity
"""
# System
import logging

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.mmclass_nt import External_Entity_i, Domain_i, Realized_Domain_i
from xuml_populate.exceptions.domain_exceptions import *

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

if __debug__:
    from xuml_populate.utility import print_mmdb

_logger = logging.getLogger(__name__)


class EE:
    """
    Populate an External Entity
    """
    tr = 'External Entity'

    @classmethod
    def populate(cls, name: str, domain: str, service_domain: str):
        """

        Args:
            name:
            domain:
            service_domain:

        Returns:

        """
        # Verify that the local domain and service domain are not the same
        if domain == service_domain:
            msg = f"Cannot populate EE since a domain cannot provide a service to itself {domain}"
            _logger.error(msg)
            raise EEPopException(msg)

        # Open a transaction for this EE and insert the EE instance
        Transaction.open(db=mmdb, name=cls.tr)
        Relvar.insert(db=mmdb, tr=cls.tr, relvar='External Entity', tuples=[
            External_Entity_i(Name=name, Domain=domain, Service_domain=service_domain)
        ])
