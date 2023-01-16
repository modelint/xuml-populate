"""
ordinal.py – Convert parsed relationshiop to a relation
"""

import logging
from PyRAL.relvar import Relvar
from typing import TYPE_CHECKING

from class_model_dsl.populate.pop_types import Ordinal_Relationship

if TYPE_CHECKING:
    from tkinter import Tk

class Ordinal:
    """
    Create an ordinal relationship relation
    """
    _logger = logging.getLogger(__name__)
    record = None
    rnum = None
    ascend = None
    oform = None

    @classmethod
    def populate(cls, mmdb: 'Tk', domain: str, rnum: str, record):
        """Constructor"""

        cls.rnum = rnum
        cls.ascend = record['ascend']
        cls.oform = record['oform']

        # Populate
        cls._logger.info(f"Populating Ordinal [{cls.rnum}]")
        Relvar.insert(relvar='Ordinal_Relationship', tuples=[
            Ordinal_Relationship(Rnum=cls.rnum, Domain=domain, Ranked_class=cls.ascend['cname'],
                                 Ranking_attribute=cls.oform['ranking attr'], Ranking_identifier=cls.oform['id'],
                                 Ascending_perspective=cls.ascend['highval'], Descending_perspective=cls.ascend['lowval']
                                 )
        ])
