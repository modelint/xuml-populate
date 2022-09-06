"""
domain.py – Convert parsed domain to a relation
"""

import logging
from class_model_dsl.populate.mm_class import MMclass

class Domain:
    """
    Create a domain relation
    """

    def __init__(self, model, parse_data):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.model = model
        self.parse_data = parse_data
        self.name = parse_data.domain

        # Insert the domain relation
        self.model.population['Domain'] = [{'Name': self.name}, ]
        # TODO: For now assume this is always a modeled domain, but need a way to specify a realized domain
        self.model.population['Modeled Domain'] = [{'Name': self.name}, ]

        # Insert classes
        for c in self.parse_data.classes:
            MMclass(domain=self, parse_data=c)

        print()