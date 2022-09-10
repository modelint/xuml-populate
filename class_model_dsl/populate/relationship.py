"""
relationship.py – Convert parsed relationship to a relation
"""

import logging

class Relationship:
    """
    Create a relationship relation
    """

    def __init__(self, domain, subsys, parse_data):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.domain = domain
        self.subsys = subsys
        self.parse_data = parse_data
        self.rnum = parse_data['rnum']

        # Populate relationship
        self.domain.model.Insert('Relationship', [self.rnum, self.domain.name])
        print()
