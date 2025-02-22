"""
relationship.py – Convert parsed relationship to a relation
"""

import logging
from xuml_populate.config import mmdb
from xuml_populate.populate.element import Element
from xuml_populate.populate.generalization import Generalization
from xuml_populate.populate.binary_association import BinaryAssociation
from xuml_populate.populate.ordinal import Ordinal
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from xuml_populate.exceptions.mp_exceptions import UnknownRelationshipType
from xuml_populate.populate.mmclass_nt import Relationship_i

_logger = logging.getLogger(__name__)

# Transactions
tr_Rel = "Relationship"

class Relationship:
    """
    Populate a Relationship
    """
    rnum = None

    @classmethod
    def populate(cls, domain: str, subsystem, record):
        """
        Populate all relevant Relationship relvars

        :param domain: The domain name
        :param subsystem: The subsystem name
        :param record: Parse of the relationship
        """

        cls.rnum = record['rnum']

        # Populate relationship
        Transaction.open(mmdb, tr_Rel)

        Element.populate_labeled_subys_element(tr=tr_Rel, label=cls.rnum, subsystem=subsystem.name, domain=domain)
        Relvar.insert(mmdb, tr=tr_Rel, relvar='Relationship', tuples=[
            Relationship_i(Rnum=cls.rnum, Domain=domain)
        ])

        # Populate based on relationship type
        if 't_side' in record:
            BinaryAssociation(tr=tr_Rel, domain=domain, rnum=cls.rnum, record=record)
        elif 'superclass' in record:
            Generalization(tr=tr_Rel, domain=domain, rnum=cls.rnum, record=record)
        elif 'ascend' in record:
            Ordinal(tr=tr_Rel, domain=domain, rnum=cls.rnum, record=record)
        else:
            _logger.error(
                "Population encountered relationship type that is not an Association, Generalization, or Ordinal.")
            raise UnknownRelationshipType
        Transaction.execute(db=mmdb, name=tr_Rel)
