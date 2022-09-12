"""
relationship.py – Convert parsed relationship to a relation
"""

import logging
from class_model_dsl.populate.generalization import Generalization
from class_model_dsl.populate.binary_association import BinaryAssociation


class Relationship:
    """
    Create a relationship relation
    """

    def __init__(self, domain, parse_data):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.domain = domain
        self.parse_data = parse_data
        self.rnum = parse_data['rnum']

        # Populate relationship
        self.domain.model.Insert('Relationship', [self.rnum, self.domain.name])


        # Populate generalization
        if 'superclass' in self.parse_data:
            Generalization(self)
        else:
            BinaryAssociation(self)