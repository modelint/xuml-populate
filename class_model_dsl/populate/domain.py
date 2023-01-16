"""
domain.py – Convert parsed domain to a relation
"""

import logging
from typing import TYPE_CHECKING
from class_model_dsl.populate.attribute import Attribute
from class_model_dsl.populate.mm_class import MMclass
from class_model_dsl.populate.relationship import Relationship
from class_model_dsl.populate.lineage import Lineage
from class_model_dsl.populate.subsystem import Subsystem
from PyRAL.transaction import Transaction
from PyRAL.relvar import Relvar
from class_model_dsl.populate.pop_types import\
    Domain_i, Modeled_Domain_i, Domain_Partition_i, Subsystem_i

if TYPE_CHECKING:
    from tkinter import Tk

class Domain:
    """
    Create a domain relation
    """
    _logger = logging.getLogger(__name__)
    subsystem_counter = {}

    @classmethod
    def populate(cls, mmdb: 'Tk', domain:Domain_i, subsystems):
        """
        Insert all user model elements in this Domain into the corresponding Metamodel classes.

        :param domain: Name of the domain
        :param mmdb:  Metamodel database
        :param name:  Name of the domain
        :param subsystems:  All parsed subsystems for the domain
        :return:
        """
        cls._logger.info(f"Populating modeled domain [{domain.Name}]")

        Transaction.open(db=mmdb)
        Relvar.insert(relvar='Domain', tuples=[ domain,])
        # # TODO: For now assume this is always a modeled domain, but need a way to specify a realized domain
        Relvar.insert(relvar='Modeled_Domain', tuples=[
            Modeled_Domain_i(Name=domain.Name),
            ])
        for s in subsystems.values():
            Relvar.insert(relvar='Subsystem', tuples=[
                Subsystem_i(Name=s.subsystem['name'], First_element_number=s.subsystem['range'][0],
                            Domain=domain.Name, Alias=s.subsystem['alias']),
            ])
            Relvar.insert(relvar='Domain_Partition', tuples=[
                Domain_Partition_i(Number=s.subsystem['range'][0], Domain=domain.Name)
            ])
        Transaction.execute()
        Relvar.relformat(db=mmdb, relvar='Domain')
        Relvar.relformat(db=mmdb, relvar='Modeled_Domain')
        Relvar.relformat(db=mmdb, relvar='Realized_Domain')
        Relvar.relformat(db=mmdb, relvar='Subsystem')
        Relvar.relformat(db=mmdb, relvar='Domain_Partition')

        # Insert classes
        for s in subsystems.values():
            subsys = Subsystem(record=s)
            for c in s.classes:
                MMclass.populate(mmdb=mmdb, domain=domain.Name, subsystem=subsys, record=c)
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
                Relationship.populate(mmdb=mmdb, domain=domain.Name, subsystem=subsys, record=r)

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
        Attribute.ResolveAttrTypes(mmdb=mmdb, domain=domain.Name)
        cls._logger.info("Populating lineage")
        # Reprinting these for lineage debugging purposes
        Lineage.Derive(mmdb=mmdb, domain=domain.Name)
        Relvar.relformat(db=mmdb, relvar='Lineage')
        Relvar.relformat(db=mmdb, relvar='Class_In_Lineage')
        print()