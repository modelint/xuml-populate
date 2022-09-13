"""
domain.py – Convert parsed domain to a relation
"""

import logging
from class_model_dsl.populate.mm_class import MMclass
from class_model_dsl.populate.relationship import Relationship
from class_model_dsl.populate.subsystem import Subsystem
from class_model_dsl.populate.lineage import Lineage

class Domain:
    """
    Create a domain relation
    """

    def __init__(self, model, parse_data):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.model = model
        self.parse_data = parse_data
        self.name = parse_data.domain['name']
        self.alias = parse_data.domain['alias']

        # Insert the domain relation
        self.logger.info(f"Populating modeled domain [{self.name}]")
        self.model.population['Domain'] = [{'Name': self.name}, {'Alias': self.alias}]
        # TODO: For now assume this is always a modeled domain, but need a way to specify a realized domain
        self.model.population['Modeled Domain'] = [{'Name': self.name}, ]

        # Insert the subsystem
        s = Subsystem(domain=self, parse_data=parse_data.subsystem)

        # Insert classes
        self.logger.info("Populating classes")
        for c in self.parse_data.classes:
            MMclass(domain=self, subsys=s, parse_data=c)

        # Insert relationships
        self.logger.info("Populating relationships")
        for r in self.parse_data.rels:
            Relationship(domain=self, parse_data=r)

        self.logger.info("Populating lineage")
        Lineage(domain=self)

