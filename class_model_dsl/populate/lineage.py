"""
lineage.py – Compute all lineage instances and populate them
"""

import logging


class Lineage:
    """
    Create all lineages for a domain
    """

    def __init__(self, domain):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.domain = domain
