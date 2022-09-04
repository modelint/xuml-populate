"""
identifier.py – Parses an xUML class model file
"""

import logging
from typing import List, Dict

header = ['Number', 'Class', 'Domain']

class Identifier:
    """
    Build an identifier for a class
    """

    def __init__(self, attributes):
        """Constructor"""
        self.logger = logging.getLogger(__name__)
        identifiers =
        for a in attributes:
