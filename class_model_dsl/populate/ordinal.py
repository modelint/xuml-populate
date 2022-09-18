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
        self.ascend = relationship.parse_data['ascend']
        self.oform = relationship.parse_data['oform']

        # Populate
        self.logger.info(f"Populating Ordinal [{self.relationship.rnum}]")
        self.relationship.domain.model.Insert('Ordinal Relationship', [
            self.relationship.rnum,
            self.relationship.domain.name,
            self.ascend['cname'],
            self.oform['ranking attr'],
            self.oform['id'],
            self.ascend['highval'],
            self.ascend['lowval'],
        ])
