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
from PyRAL.relation import Relation
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
        """
        cls._logger.info(f"Populating modeled domain [{domain.Name}]")

        Transaction.open(tclral=mmdb)
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
        Relation.print(mmdb, 'Domain')
        Relation.print(mmdb, 'Modeled_Domain')
        Relation.print(mmdb, 'Realized_Domain')
        Relation.print(mmdb, 'Subsystem')
        Relation.print(mmdb, 'Domain_Partition')

        # Insert classes
        for s in subsystems.values():
            subsys = Subsystem(record=s)
            for c in s.classes:
                MMclass.populate(mmdb=mmdb, domain=domain.Name, subsystem=subsys, record=c)
        Relation.print(mmdb, 'Class')
        Relation.print(mmdb, 'Alias')
        Relation.print(mmdb, 'Attribute')
        Relation.print(mmdb, 'Identifier')
        Relation.print(mmdb, 'Super_Identifier')
        Relation.print(mmdb, 'Irreducible_Identifier')
        Relation.print(mmdb, 'Identifier_Attribute')
        Relation.print(mmdb, 'Non_Derived_Attribute')

        # Insert relationships
        cls._logger.info("Populating user model relationships")
        for s in subsystems.values():
            subsys = Subsystem(record=s)
            for r in s.rels:
                Relationship.populate(mmdb=mmdb, domain=domain.Name, subsystem=subsys, record=r)

        Relation.print(mmdb, 'Relationship')
        Relation.print(mmdb, 'Association')
        Relation.print(mmdb, 'Binary_Association')
        Relation.print(mmdb, 'Perspective')
        Relation.print(mmdb, 'Asymmetric_Perspective')
        Relation.print(mmdb, 'T_Perspective')
        Relation.print(mmdb, 'P_Perspective')
        Relation.print(mmdb, 'Association_Class')
        Relation.print(mmdb, 'Generalization')
        Relation.print(mmdb, 'Superclass')
        Relation.print(mmdb, 'Subclass')
        Relation.print(mmdb, 'Facet')
        Relation.print(mmdb, 'Minimal_Partition')
        Relation.print(mmdb, 'Ordinal_Relationship')
        Relation.print(mmdb, 'Reference')
        Relation.print(mmdb, 'Association_Reference')
        Relation.print(mmdb, 'Simple_Association_Reference')
        Relation.print(mmdb, 'Referring_Class')
        Relation.print(mmdb, 'Association_Class_Reference')
        Relation.print(mmdb, 'T_Reference')
        Relation.print(mmdb, 'P_Reference')
        Relation.print(mmdb, 'Generalization_Reference')
        Relation.print(mmdb, 'Formalizing_Class_Role')
        Relation.print(mmdb, 'Attribute_Reference')
        Attribute.ResolveAttrTypes(mmdb=mmdb, domain=domain.Name)
        cls._logger.info("Populating lineage")
        # Reprinting these for lineage debugging purposes
        Lineage.Derive(mmdb=mmdb, domain=domain.Name)
        Relation.print(mmdb, 'Lineage')
        Relation.print(mmdb, 'Class_In_Lineage')
        print()