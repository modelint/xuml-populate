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
from class_model_dsl.populate.state_model import StateModel
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
    def populate(cls, mmdb: 'Tk', domain:Domain_i, subsystems, statemodels):
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

        # Insert classes
        for s in subsystems.values():
            subsys = Subsystem(record=s)
            cls._logger.info("Populating classes")
            for c in s.classes:
                MMclass.populate(mmdb=mmdb, domain=domain.Name, subsystem=subsys, record=c)
            cls._logger.info("Populating relationships")
            for r in s.rels:
                Relationship.populate(mmdb=mmdb, domain=domain.Name, subsystem=subsys, record=r)
            cls._logger.info("Populating state models")
            for sm in statemodels.values():
                StateModel.populate(mmdb, subsys=subsys.name, sm=sm)

        Attribute.ResolveAttrTypes(mmdb=mmdb, domain=domain.Name)
        cls._logger.info("Populating lineage")

        # Reprinting these for lineage debugging purposes
        Lineage.Derive(mmdb=mmdb, domain=domain.Name)

        # Print out the populated metamodel
        Relvar.printall(mmdb)
        pass

