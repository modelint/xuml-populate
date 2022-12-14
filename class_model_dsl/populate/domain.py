"""
domain.py – Convert parsed domain to a relation
"""

import logging
# from class_model_dsl.populate.mm_class import MMclass
# from class_model_dsl.populate.relationship import Relationship
# from class_model_dsl.populate.subsystem import Subsystem
from collections import namedtuple
from PyRAL.transaction import Transaction
from PyRAL.relvar import Relvar

Domain_i = namedtuple('Domain_i', 'Name Alias')
Modeled_Domain_i = namedtuple('Modeled_Domain_i', 'Name')
Domain_Partition_i = namedtuple('Domain_Partition_i', 'Number Domain')
Subsystem_i = namedtuple('Domain_Partition_i', 'Name First_element_number, Domain Alias')

class Domain:
    """
    Create a domain relation
    """
    _logger = logging.getLogger(__name__)

    @classmethod
    def populate(cls, db, domain, subsystems):
        """

        :param domain:
        :param db:
        :param name:  # Name of the domain
        :param subsystems:  # All parsed subsystems for the domain
        :return:
        """
        cls._logger.info(f"Populating modeled domain [{domain['name']}]")

        Transaction.open(db)
        Relvar.insert(db=db, relvar='Domain', tuples=[
            Domain_i(Name=domain['name'], Alias=domain['alias']),
            ])
        Relvar.insert(db=db, relvar='Modeled_Domain', tuples=[
            Modeled_Domain_i(Name=domain['name']),
            ])
        for s in subsystems.values():
            Relvar.insert(db=db, relvar='Subsystem', tuples=[
                Subsystem_i(Name=s.subsystem['name'], First_element_number=s.subsystem['range'][0],
                            Domain=domain['name'], Alias=s.subsystem['alias']),
            ])
            Relvar.insert(db=db, relvar='Domain_Partition', tuples=[
                Domain_Partition_i(Number=s.subsystem['range'][0], Domain=domain['name'])
            ])
        Transaction.execute()
        pass




        # self.lnums = 0
        #
        # # Insert the domain relation
        # self.logger.info(f"Populating modeled domain [{cls.name}]")
        # self.model.population['Domain'] = [{'Name': self.name, 'Alias': self.alias}, ]
        # # TODO: For now assume this is always a modeled domain, but need a way to specify a realized domain
        # self.model.population['Modeled Domain'] = [{'Name': self.name}, ]
        #
        # # Insert the subsystem
        # s = Subsystem(domain=self, parse_data=parse_data.subsystem)
        #
        # # Insert classes
        # self.logger.info("Populating classes")
        # for c in self.parse_data.classes:
        #     MMclass(domain=self, subsys=s, parse_data=c)
        #
        # # Insert relationships
        # self.logger.info("Populating relationships")
        # for r in self.parse_data.rels:
        #     Relationship(domain=self, subsys=s, parse_data=r)

