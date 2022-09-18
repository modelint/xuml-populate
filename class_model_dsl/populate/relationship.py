"""
relationship.py – Convert parsed relationship to a relation
"""

import logging
from class_model_dsl.populate.generalization import Generalization
from class_model_dsl.populate.binary_association import BinaryAssociation
from class_model_dsl.populate.ordinal import Ordinal
from class_model_dsl.mp_exceptions import UnknownRelationshipType


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

        # Populate subsystem element
        se_values = dict(
            zip(self.domain.model.table_headers['Subsystem Element'], [self.rnum, self.domain.name, self.subsys.name])
        )
        self.domain.model.population['Subsystem Element'].append(se_values)

        # Populate element
        e_values = dict(
            zip(self.domain.model.table_headers['Element'], [self.rnum, self.domain.name])
        )
        self.domain.model.population['Element'].append(e_values)

        # Populate generalization
        if 't_side' in self.parse_data:
            BinaryAssociation(self)
        elif 'superclass' in self.parse_data:
            Generalization(self)
        elif 'ascend' in self.parse_data:
            Ordinal(self)
        else:
            logging.error(
                "Population encountered relationship type that is not an Association, Generalization, or Ordinal.")
            raise UnknownRelationshipType
