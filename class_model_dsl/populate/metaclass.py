"""
metaclass.py – Convert parsed class to a relation
"""

import logging
from class_model_dsl.populate.metaclass_headers import header
from typing import List, Dict

class Metaclass:
    """
    Build an identifier for a class
    """

    def __init__(self, metaclass):
        """Constructor"""
        self.logger = logging.getLogger(__name__)
