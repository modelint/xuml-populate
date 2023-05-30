"""
ee.py – Convert external entity to a relation
"""

import logging
from PyRAL.transaction import Transaction
from PyRAL.relvar import Relvar
from class_model_dsl.populate.element import Element
from class_model_dsl.populate.operation import Operation
from class_model_dsl.populate.pop_types import EE_i

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
    def populate(cls, mmdb: 'Tk', ee_name: str, class_name:str, subsys_name: str, domain_name: str):
        """
        :param mmdb:
        :param ee_name:
        :param class_name:
        :param subsys_name:
        :param domain_name:
        :return:
        """
        # Populate ee
        cls._logger.info(f"Populating ee [{ee_name}]")
        cls._logger.info(f"Transaction open: Populate EE")
        Transaction.open(tclral=mmdb) # Create an EE with at least one Operation
        EEnum = Element.populate_unlabeled_subsys_element(mmdb,
                                                         prefix='EE',
                                                         subsystem_name=subsys_name, domain_name=domain_name)
        Relvar.insert(relvar='External_Entity', tuples=[
            EE_i(EEnum=EEnum, Name=ee_name, Class=class_name, Domain=domain_name)
        ])

        # Add operations
        first_op = True
        for opfile in (cls.subsys_ee_path / ee_name).glob("*.op"):
            Operation.populate(mmdb=mmdb, domain_name=domain_name,
                               subsys_name=subsys_name, opfile=opfile, first_op=first_op)
            if first_op:
                first_op = False