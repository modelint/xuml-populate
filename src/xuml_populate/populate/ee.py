"""
ee.py – Convert external entity to a relation
"""

import logging
from xuml_populate.config import mmdb
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from xuml_populate.populate.element import Element
from xuml_populate.populate.operation import Operation
from xuml_populate.populate.mmclass_nt import External_Entity_i

_logger = logging.getLogger(__name__)

# Transactions
tr_EE = "EE"

class EE:
    """
    Populate all relevant External Entity relvars
    """
    subsys_ee_path = None
    record = None

    @classmethod
    def populate(cls, ee_name: str, subsys: str, domain: str, op_parse):
        """
        Populate an External Entity

        :param ee_name: The EE name
        :param cname: The proxy Class name
        :param subsys: The name of the subsystem
        :param domain: The name of the domain
        """
        # Class name can be obtained from the parse of any operation
        cname = next(iter(op_parse.values())).cname
        # Populate ee
        _logger.info(f"Populating ee [{ee_name}]")
        _logger.info(f"Transaction open: Populate EE")
        Transaction.open(mmdb, tr_EE)  # Create an EE with at least one Operation
        EEnum = Element.populate_unlabeled_subsys_element(tr=tr_EE, prefix='EE', subsystem=subsys, domain=domain)
        Relvar.insert(mmdb, tr=tr_EE, relvar='External_Entity', tuples=[
            External_Entity_i(EEnum=EEnum, Name=ee_name, Class=cname, Domain=domain)
        ])

        # Add operations
        tr = tr_EE  # Start out by completing the required op for the EE
        for op in op_parse.values():
            tr = Operation.populate(tr=tr, domain=domain, subsys=subsys, parsed_op=op)
            # "EE" (tr_EE) closes on first operation and all subsequent tr values will be "Operation"

