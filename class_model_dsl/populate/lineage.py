"""
lineage.py – Compute all lineage instances and populate them
"""

import logging
from class_model_dsl.database.sm_meta_db import SMmetaDB as smdb
from sqlalchemy import select, join, and_

class Lineage:
    """
    Create all lineages for a domain
    """

    def __init__(self, domain):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.domain = domain
        self.logger.info(f"Skipping lineage for now")
        self.leaf = {}

        leaf_classes = None
        # Get all classes with no superclass facets and at least on subclass facet
        subclass_t = smdb.MetaData.tables['Subclass']


    def Trace(self, key, c, rel, lineage):
        """
        Add classes to a leaf lineage
        """
