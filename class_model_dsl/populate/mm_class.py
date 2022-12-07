"""
mm_class.py – Convert parsed class to a relation
"""

import logging
from class_model_dsl.populate.attribute import Attribute

class MMclass:
    """
    Create a class relation
    """

    @classmethod
    def populate(cls, domain, parse_data):
        """Constructor"""
        pass
        # cls.logger = logging.getLogger(__name__)
        #
        # cls.domain = domain
        # self.subsys = subsys
        # self.parse_data = parse_data
        # self.name = parse_data['name']
        # self.attributes = parse_data['attributes']
        # self.identifiers = set()
        # self.alias = parse_data.get('alias')  # Optional
        #
        # # Get the next cnum
        # cnum = self.subsys.next_cnum()
        #
        # # Populate class
        # self.logger.info(f"Populating class [{self.name}]")
        # class_values = dict(
        #     zip(self.domain.model.table_headers['Class'], [self.parse_data['name'], cnum, self.domain.name])
        # )
        # self.domain.model.population['Class'].append(class_values)
        #
        # # Populate subsystem element
        # se_values = dict(
        #     zip(self.domain.model.table_headers['Subsystem Element'], [cnum, self.domain.name, self.subsys.name])
        # )
        # self.domain.model.population['Subsystem Element'].append(se_values)
        #
        # # Populate element
        # e_values = dict(
        #     zip(self.domain.model.table_headers['Element'], [cnum, self.domain.name])
        # )
        # self.domain.model.population['Element'].append(e_values)
        #
        # # Populate optional alias
        # if self.alias:
        #     alias_values = dict(
        #         zip(self.domain.model.table_headers['Alias'], [self.alias, self.name, self.domain.name])
        #     )
        #     self.domain.model.population['Alias'].append(alias_values)
        #
        # for a in self.attributes:
        #     Attribute(mmclass=self, parse_data=a)