"""
attribute.py – Create an attribute relation
"""

import logging

class Attribute:
    """
    Build all attributes for a class
    """
    def __init__(self, mmclass, parse_data):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.mmclass = mmclass
        self.parse_data = parse_data
        self.type = parse_data.get('type', "<unresolved>")
        self.identifiers = self.parse_data.get('I', [])  # This attr might not participate in any identifier

        attr_values = dict(
            zip(self.mmclass.domain.model.table_headers['Attribute'],
            [self.parse_data['name'], self.mmclass.name, self.mmclass.domain.name, self.type])
        )
        self.mmclass.domain.model.population['Attribute'].append(attr_values)
        # TODO: Check for derived or non-derived, for now assume the latter
        self.mmclass.domain.model.population['Non Derived Attribute'].append(attr_values)

        for i in self.identifiers:
            # Add Identifier if it is not already in the population
            if i not in self.mmclass.identifiers:
                id_values = dict(
                    zip(self.mmclass.domain.model.table_headers['Identifier'],
                        [i, self.mmclass.name, self.mmclass.domain.name])
                )
                self.mmclass.domain.model.population['Identifier'].append(id_values)
                # TODO: Check for super or irreducible, for now assume the latter
                self.mmclass.domain.model.population['Irreducible Identifier'].append(id_values)
                self.mmclass.identifiers.add(i)

            # Include this attribute in the each of its identifiers
            id_attr_values = dict(
                zip(self.mmclass.domain.model.table_headers['Identifier Attribute'],
                    [i, self.parse_data['name'], self.mmclass.name, self.mmclass.domain.name])
            )
            self.mmclass.domain.model.population['Identifier Attribute'].append(id_attr_values)