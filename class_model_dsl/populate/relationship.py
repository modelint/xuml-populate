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
        self.tside = parse_data['t_side']
        self.pside = parse_data['p_side']
        print()