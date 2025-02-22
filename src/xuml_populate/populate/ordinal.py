"""
ordinal.py – Process a parsed ordinal relationship to populate the metamodel db
"""

# System
import logging

# Model Integration
from pyral.relvar import Relvar

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.mmclass_nt import Ordinal_Relationship_i

_logger = logging.getLogger(__name__)

class Ordinal:
    """
    Populate all relevant Ordinal Relationship relvars
    """
    rnum = None
    ascend = None
    oform = None

    def __init__(self, tr: str, domain: str, rnum: str, record):
        """
        Populate an Ordinal Relationship

        :param tr: The name of the open transaction
        :param domain: The domain name
        :param rnum: The relationship name
        :param record: The relationship parse record
        """

        self.rnum = rnum
        self.ascend = record['ascend']
        self.oform = record['oform']

        # Populate
        _logger.info(f"Populating Ordinal [{self.rnum}]")
        Relvar.insert(db=mmdb, tr=tr, relvar='Ordinal_Relationship', tuples=[
            Ordinal_Relationship_i(Rnum=self.rnum, Domain=domain, Ranked_class=self.ascend['cname'],
                                   Ranking_attribute=self.oform['ranking attr']['name'], Ranking_identifier=self.oform['id'],
                                   Ascending_perspective=self.ascend['highval'],
                                   Descending_perspective=self.ascend['lowval']
                                   )
        ])
