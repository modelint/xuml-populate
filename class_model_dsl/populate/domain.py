"""
domain.py – Convert parsed domain to a relation
"""

import logging
from class_model_dsl.populate.mm_class import MMclass
# from class_model_dsl.populate.relationship import Relationship
from class_model_dsl.populate.subsystem import Subsystem
from collections import namedtuple
from PyRAL.transaction import Transaction
from PyRAL.relvar import Relvar

Domain_i = namedtuple('Domain_i', 'Name Alias')
Modeled_Domain_i = namedtuple('Modeled_Domain_i', 'Name')
Domain_Partition_i = namedtuple('Domain_Partition_i', 'Number Domain')
Subsystem_i = namedtuple('Domain_Partition_i', 'Name First_element_number Domain Alias')

class Domain:
    """
    Create a domain relation
    """
    _logger = logging.getLogger(__name__)
    subsystem_counter = {}
    lnums = 0

    @classmethod
    def populate(cls, mmdb, domain, subsystems):
        """

        :param domain:
        :param mmdb:  Metamodel database
        :param name:  Name of the domain
        :param subsystems:  All parsed subsystems for the domain
        :return:
        """
        cls._logger.info(f"Populating modeled domain [{domain['name']}]")

        Transaction.open(db=mmdb)
        Relvar.insert(db=mmdb, relvar='Domain', tuples=[
            Domain_i(Name=domain['name'], Alias=domain['alias']),
            ])
        # # TODO: For now assume this is always a modeled domain, but need a way to specify a realized domain
        Relvar.insert(db=mmdb, relvar='Modeled_Domain', tuples=[
            Modeled_Domain_i(Name=domain['name']),
            ])
        for s in subsystems.values():
            Relvar.insert(db=mmdb, relvar='Subsystem', tuples=[
                Subsystem_i(Name=s.subsystem['name'], First_element_number=s.subsystem['range'][0],
                            Domain=domain['name'], Alias=s.subsystem['alias']),
            ])
            Relvar.insert(db=mmdb, relvar='Domain_Partition', tuples=[
                Domain_Partition_i(Number=s.subsystem['range'][0], Domain=domain['name'])
            ])
        Transaction.execute()
        domain_pop = Relvar.population(db=mmdb, relvar='Domain')
        modeled_domain_pop = Relvar.population(db=mmdb, relvar='Modeled_Domain')
        subsystem_pop = Relvar.population(db=mmdb, relvar='Subsystem')
        domain_partition_pop = Relvar.population(db=mmdb, relvar='Domain_Partition')
        cls._logger.info("Domain subsytem population:")
        cls._logger.info(f"Domain Population\n{domain_pop}")
        cls._logger.info(f"Modeled Domain\n{modeled_domain_pop}")
        cls._logger.info(f"Subsystem\n{subsystem_pop}")
        cls._logger.info(f"Domain Paritition\n{domain_partition_pop}")

        # Insert classes
        for s in subsystems.values():
            subsys = Subsystem(record=s)
            for c in s.classes:
                MMclass.populate(mmdb=mmdb, domain=domain, subsystem=subsys, record=c)
            Relvar.relformat(db=mmdb, relvar='Class')
        pass

        #
        # # Insert relationships
        # self.logger.info("Populating relationships")
        # for r in self.parse_data.rels:
        #     Relationship(domain=self, subsys=s, parse_data=r)

