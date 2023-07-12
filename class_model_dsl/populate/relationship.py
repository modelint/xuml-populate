"""
relationship.py – Convert parsed relationship to a relation
"""

import logging
from class_model_dsl.populate.element import Element
from class_model_dsl.populate.generalization import Generalization
from class_model_dsl.populate.binary_association import BinaryAssociation
from class_model_dsl.populate.ordinal import Ordinal
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from class_model_dsl.mp_exceptions import UnknownRelationshipType
from typing import TYPE_CHECKING
from class_model_dsl.populate.pop_types import Rel_i

if TYPE_CHECKING:
    from tkinter import Tk


class Relationship:
    """
    Create a relationship relation
    """
    _logger = logging.getLogger(__name__)
    record = None
    name = None
    rnum = None

    @classmethod
    def populate(cls, mmdb: 'Tk', domain: str, subsystem, record):
        """Constructor"""

        cls.record = record
        cls.rnum = record['rnum']

        # Populate relationship
        Transaction.open(tclral=mmdb)

        Element.populate_labeled_subys_element(mmdb, label=cls.rnum, subsystem_name=subsystem.name, domain_name=domain)
        Relvar.insert(relvar='Relationship', tuples=[
            Rel_i(Rnum=cls.rnum, Domain=domain)
        ])

        # Populate based on relationship type
        if 't_side' in cls.record:
            BinaryAssociation.populate(mmdb, domain, cls.rnum, cls.record)
        elif 'superclass' in cls.record:
            Generalization.populate(mmdb, domain, cls.rnum, cls.record)
        elif 'ascend' in cls.record:
            Ordinal.populate(mmdb, domain, cls.rnum, cls.record)
        else:
            logging.error(
                "Population encountered relationship type that is not an Association, Generalization, or Ordinal.")
            raise UnknownRelationshipType
        Transaction.execute()
