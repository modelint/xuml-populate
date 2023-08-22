"""
ee.py – Convert external entity to a relation
"""

import logging
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from xuml_populate.populate.element import Element
from xuml_populate.populate.operation import Operation
from xuml_populate.populate.mmclass_nt import External_Entity_i

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tkinter import Tk



class EE:
    """
    Create an External Entity relation
    """
    _logger = logging.getLogger(__name__)
    subsys_ee_path = None
    record = None

    @classmethod
    def populate(cls, mmdb: 'Tk', ee_name: str, subsys_name: str, domain_name: str, op_parse):
        """
        :param mmdb:
        :param ee_name:
        :param class_name:
        :param subsys_name:
        :param domain_name:
        :return:
        """
        # Class name can be obtained from the parse of any operation
        cname = next(iter(op_parse.values())).cname
        # Populate ee
        cls._logger.info(f"Populating ee [{ee_name}]")
        cls._logger.info(f"Transaction open: Populate EE")
        Transaction.open(tclral=mmdb)  # Create an EE with at least one Operation
        EEnum = Element.populate_unlabeled_subsys_element(mmdb,
                                                         prefix='EE',
                                                         subsystem_name=subsys_name, domain_name=domain_name)
        Relvar.insert(relvar='External_Entity', tuples=[
            External_Entity_i(EEnum=EEnum, Name=ee_name, Class=cname, Domain=domain_name)
        ])

        # Add operations
        first_op = True
        for op in op_parse.values():
            Operation.populate(mmdb=mmdb, domain_name=domain_name, subsys_name=subsys_name, parsed_op=op,
                               first_op=first_op)
            if first_op:
                first_op = False


