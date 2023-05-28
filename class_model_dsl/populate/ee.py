"""
ee.py – Convert external entity to a relation
"""

import logging
from PyRAL.transaction import Transaction
from PyRAL.relvar import Relvar
from class_model_dsl.populate.element import Element
from class_model_dsl.populate.pop_types import Ex
from pathlib import Path

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
    def populate(cls, mmdb: 'Tk', ee_name: str, subsys_name: str, domain_name: str):
        """
        :param mmdb:
        :param ee_name:
        :param subsys_name:
        :param domain_name:
        :return:
        """
        # Populate ee
        cls._logger.info(f"Populating ee [{ee_name}]")
        Transaction.open(tclral=mmdb)
        EEnum = Element.populate_unlabeled_subsys_element(mmdb,
                                                         prefix='EE',
                                                         subsystem_name=subsys_name, domain_name=domain_name)
        Relvar.insert(relvar='External_Entity', tuples=[
            Ee
        ])
        Transaction.execute()

        # Add operations
        Op.populate(mmdb, domain_name=domain, subsys_name=subsystem.name, class_name=cls.name)

        # Add EE and ops