"""
mm_class.py – Convert parsed class to a relation
"""

import logging
from class_model_dsl.populate.attribute import Attribute

class MMclass:
    """
    Create a class relation
    """

    def __init__(self, domain, model, parse_data):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.domain = domain
        self.model = model
        self.parse_data = parse_data
        self.name = parse_data['name']
        self.attributes = parse_data['attributes']
        self.identifiers = set()
        self.alias = parse_data.get('alias')  # Optional

        # Populate class
        class_values = dict(
            zip(self.model.table_headers['Class'], [self.parse_data['name'], self.domain])
        )
        self.model.population['Class'].append(class_values)

        # Populate optional alias
        if self.alias:
            alias_values = dict(
                zip(self.model.table_headers['Alias'], [self.parse_data['name'], self.name, self.domain])
            )
            self.model.population['Alias'].append(alias_values)

        for a in self.attributes:
            Attribute(mmclass=self, parse_data=a)

        print()