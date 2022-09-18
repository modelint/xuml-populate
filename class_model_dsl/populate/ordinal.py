"""
ordinal.py – Convert parsed relationshiop to a relation
"""

import logging

class Ordinal:
    """
    Create an ordinal relationship relation
    """

    def __init__(self, relationship):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.relationship = relationship
