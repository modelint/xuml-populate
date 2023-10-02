"""
ordinal.py – Process a parsed ordinal relationship to populate the metamodel db
"""

import logging
from pyral.relvar import Relvar
from xuml_populate.populate.mmclass_nt import Ordinal_Relationship_i

_logger = logging.getLogger(__name__)

class Ordinal:
    """
    Populate all relevant Ordinal Relationship relvars
    """
    rnum = None
    ascend = None
    oform = None

    @classmethod
    def populate(cls, mmdb: str, tr: str, domain: str, rnum: str, record):
        """
        Populate an Ordinal Relationship

        :param mmdb: The metamodel db name
        :param tr: The name of the open transaction
        :param domain: The domain name
        :param rnum: The relationship name
        :param record: The relationship parse record
        """

        cls.rnum = rnum
        cls.ascend = record['ascend']
        cls.oform = record['oform']

        # Populate
        _logger.info(f"Populating Ordinal [{cls.rnum}]")
        Relvar.insert(mmdb, tr=tr, relvar='Ordinal_Relationship', tuples=[
            Ordinal_Relationship_i(Rnum=cls.rnum, Domain=domain, Ranked_class=cls.ascend['cname'],
                                   Ranking_attribute=cls.oform['ranking attr'], Ranking_identifier=cls.oform['id'],
                                   Ascending_perspective=cls.ascend['highval'],
                                   Descending_perspective=cls.ascend['lowval']
                                   )
        ])
