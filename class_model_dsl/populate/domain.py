"""
domain.py – Convert parsed domain to a relation
"""

import logging
from class_model_dsl.populate.attribute import Attribute
from class_model_dsl.populate.mm_class import MMclass
from class_model_dsl.populate.relationship import Relationship
from class_model_dsl.populate.subsystem import Subsystem
from PyRAL.transaction import Transaction
from PyRAL.relvar import Relvar
from class_model_dsl.populate.pop_types import\
    Domain_i, Modeled_Domain_i, Domain_Partition_i, Subsystem_i

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
        Relvar.relformat(db=mmdb, relvar='Domain')
        modeled_domain_pop = Relvar.population(db=mmdb, relvar='Modeled_Domain')
        Relvar.relformat(db=mmdb, relvar='Modeled_Domain')
        Relvar.relformat(db=mmdb, relvar='Realized_Domain')
        subsystem_pop = Relvar.population(db=mmdb, relvar='Subsystem')
        Relvar.relformat(db=mmdb, relvar='Subsystem')
        domain_partition_pop = Relvar.population(db=mmdb, relvar='Domain_Partition')
        Relvar.relformat(db=mmdb, relvar='Domain_Partition')
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
        Relvar.relformat(db=mmdb, relvar='Alias')
        Relvar.relformat(db=mmdb, relvar='Attribute')
        Relvar.relformat(db=mmdb, relvar='Identifier')
        Relvar.relformat(db=mmdb, relvar='Super_Identifier')
        Relvar.relformat(db=mmdb, relvar='Irreducible_Identifier')
        Relvar.relformat(db=mmdb, relvar='Identifier_Attribute')
        Relvar.relformat(db=mmdb, relvar='Non_Derived_Attribute')

        # Insert relationships
        cls._logger.info("Populating user model relationships")
        for s in subsystems.values():
            subsys = Subsystem(record=s)
            for r in s.rels:
                Relationship.populate(mmdb=mmdb, domain=domain, subsystem=subsys, record=r)

        Relvar.relformat(db=mmdb, relvar='Relationship')
        Relvar.relformat(db=mmdb, relvar='Association')
        Relvar.relformat(db=mmdb, relvar='Binary_Association')
        Relvar.relformat(db=mmdb, relvar='Perspective')
        Relvar.relformat(db=mmdb, relvar='Asymmetric_Perspective')
        Relvar.relformat(db=mmdb, relvar='T_Perspective')
        Relvar.relformat(db=mmdb, relvar='P_Perspective')
        Relvar.relformat(db=mmdb, relvar='Association_Class')
        Relvar.relformat(db=mmdb, relvar='Generalization')
        Relvar.relformat(db=mmdb, relvar='Superclass')
        Relvar.relformat(db=mmdb, relvar='Subclass')
        Relvar.relformat(db=mmdb, relvar='Facet')
        Relvar.relformat(db=mmdb, relvar='Minimal_Partition')
        Relvar.relformat(db=mmdb, relvar='Ordinal_Relationship')
        Relvar.relformat(db=mmdb, relvar='Reference')
        Relvar.relformat(db=mmdb, relvar='Association_Reference')
        Relvar.relformat(db=mmdb, relvar='Simple_Association_Reference')
        Relvar.relformat(db=mmdb, relvar='Referring_Class')
        Relvar.relformat(db=mmdb, relvar='Association_Class_Reference')
        Relvar.relformat(db=mmdb, relvar='T_Reference')
        Relvar.relformat(db=mmdb, relvar='P_Reference')
        Relvar.relformat(db=mmdb, relvar='Generalization_Reference')
        Relvar.relformat(db=mmdb, relvar='Formalizing_Class_Role')
        Relvar.relformat(db=mmdb, relvar='Attribute_Reference')
        print("Done")
        Attribute.ResolveAttrTypes(mmdb=mmdb)
        pass
