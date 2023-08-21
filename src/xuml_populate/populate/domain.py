"""
domain_name.py – Convert parsed domain_name to a relation
"""

import logging
from typing import TYPE_CHECKING, Dict
from pathlib import Path
# from class_model_dsl.populate.attribute import Attribute
from xuml_populate.populate.mm_class import MMclass
# from class_model_dsl.populate.method import Method
# from class_model_dsl.populate.relationship import Relationship
# from class_model_dsl.populate.ee import EE
# from class_model_dsl.populate.method import Method
# from class_model_dsl.populate.lineage import Lineage
from xuml_populate.populate.subsystem import Subsystem
# from class_model_dsl.populate.state_model import StateModel
# from class_model_dsl.populate.activity import Activity
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from xuml_populate.populate.mmclass_nt import Domain_i, Modeled_Domain_i, Domain_Partition_i, Subsystem_i

if TYPE_CHECKING:
    from tkinter import Tk

class Domain:
    """
    Create a domain_name relation
    """
    _logger = logging.getLogger(__name__)
    subsystem_counter = {}
    types = None

    @classmethod
    def populate(cls, mmdb: 'Tk', domain: str, content: Dict):
        """
        Insert all user model elements in this Domain into the corresponding Metamodel classes.

        :param mmdb:  The metamodel database
        :param domain:  The name of the domain extracted from the content
        :param content:  The parsed content of the domain
        """
        cls._logger.info(f"Populating modeled domain_name [{domain}]")
        cls._logger.info(f"Transaction open: domain and subsystems [{domain}]")
        Transaction.open(tclral=mmdb)  # Modeled domain

        Relvar.insert(relvar='Domain', tuples=[
            Domain_i(Name=domain, Alias=content['alias']),
        ])
        # TODO: For now assume this is always a modeled domain_name, but need a way to specify a realized domain_name
        Relvar.insert(relvar='Modeled_Domain', tuples=[
            Modeled_Domain_i(Name=domain),
            ])
        pass
        for cm_parse in content['subsystems'].values():
            subsys = cm_parse['class_model'].subsystem
            Relvar.insert(relvar='Subsystem', tuples=[
                Subsystem_i(Name=subsys['name'], First_element_number=subsys['range'][0],
                            Domain=domain, Alias=subsys['alias']),
            ])
            Relvar.insert(relvar='Domain_Partition', tuples=[
                Domain_Partition_i(Number=subsys['range'][0], Domain=domain)
            ])
        Transaction.execute()  # Modeled domain
        cls._logger.info(f"Transaction closed: domain and subsystems [{domain}]")
        pass

        # Insert classes
        for cm_parse in content['subsystems'].values():
            subsys = Subsystem(subsys_parse=cm_parse['class_model'].subsystem)
            cls._logger.info("Populating classes")
            for c in cm_parse['class_model'].classes:
                MMclass.populate(mmdb=mmdb, domain=domain, subsystem=subsys, record=c)
            cls._logger.info("Populating relationships")
        #     for r in s.rels:
        #         Relationship.populate(mmdb=mmdb, domain=domain.Name, subsystem=subsys, subsys_parse=r)
        #     cls._logger.info("Populating methods and operations")
        #     for c in s.classes:
        #         # All classes must be populated first, so that parameter types in signatures can be resolved
        #         # as class or non-class types
        #         Method.populate(mmdb, domain_name=domain.Name, subsys_name=subsys.name, class_name=c['name'])
        #         # Add EE and ops
        #         if ee_name := c.get('ee'):
        #             EE.populate(mmdb, ee_name=ee_name, class_name=c['name'], subsys_name=subsys.name,
        #                         domain_name=domain.Name)
        #     cls._logger.info("Populating state models")
        #     for sm in statemodels.values():
        #         StateModel.populate(mmdb, subsys=subsys.name, sm=sm)
        #
        # Attribute.ResolveAttrTypes(mmdb=mmdb, domain=domain.Name)
        # cls._logger.info("Populating lineage")
        #
        # # Reprinting these for lineage debugging purposes
        # Lineage.Derive(mmdb=mmdb, domain=domain.Name)
        #
        # # Print out the populated metamodel
        # # Relvar.printall(mmdb)
        #
        # # Populate actions for all Activities
        # Activity.process_statements(mmdb)
        # pass
        #
