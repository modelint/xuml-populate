"""
lineage.py – Compute all lineage instances and populate them
"""

import logging
from class_model_dsl.database.sm_meta_db import SMmetaDB as smdb
from sqlalchemy import select
from typing import List, Set, Optional


class Lineage:
    """
    Create all lineages for a domain
    """

    def __init__(self, domain):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.domain = domain
        self.walks = []

        # Get all classes with at least one subclass facet and no superclass facets as: leaves

        subclass_t = smdb.MetaData.tables['Subclass']
        superclass_t = smdb.MetaData.tables['Superclass']
        psuper = [superclass_t.c.Class, superclass_t.c.Domain]
        psub = [subclass_t.c.Class, subclass_t.c.Domain]
        q = select(psub).except_(select(psuper))
        rows = smdb.Connection.execute(q).fetchall()
        self.leaf_classes = [r['Class'] for r in rows]
        for leaf in self.leaf_classes:
            leafwalk = self.Step(walk=[], cvisit=leaf, xrels=set())
            self.walks.append(leafwalk)
        print()

    def Step(self, walk: List, cvisit: str, xrels: Set[int], rvisit: Optional[int] = None) -> List:
        """

        :param walk:
        :param cvisit:
        :param rvisit:
        :param xrels:
        :return:
        """
        walk.append(cvisit)
        return walk
