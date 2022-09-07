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
        self.name = parse_data['name']
        self.attributes = parse_data['attributes']
        self.identifiers = set()
        self.alias = parse_data.get('alias')  # Optional