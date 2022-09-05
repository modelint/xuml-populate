"""
attribute.py – Create an attribute relation
"""

import logging
from typing import List, Dict

class Attribute:
    """
    Build all attributes for a class
    """
    def __init__(self, mmclass, parse_data):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.mmclass = mmclass
        self.parse_data = parse_data
        self.identifiers = []

        attr_values = dict(
            zip(self.mmclass.model.table_headers['Attribute'], [self.parse_data['name'], self.mmclass.name, self.mmclass.domain])
        )
        self.mmclass.model.population['Attribute'].append(attr_values)
