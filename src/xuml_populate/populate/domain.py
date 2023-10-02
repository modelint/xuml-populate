"""
domain.py – Process parsed domain to populate the metamodel db
"""

import logging
from typing import Dict
from xuml_populate.populate.attribute import Attribute
from xuml_populate.populate.mm_class import MMclass
from xuml_populate.populate.method import Method
from xuml_populate.populate.relationship import Relationship
from xuml_populate.populate.ee import EE
from xuml_populate.populate.lineage import Lineage
from xuml_populate.populate.subsystem import Subsystem
from xuml_populate.populate.state_model import StateModel
from xuml_populate.populate.activity import Activity
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from pyral.relvar import Relation  # For debugging
from xuml_populate.populate.mmclass_nt import Domain_i, Modeled_Domain_i, Domain_Partition_i, Subsystem_i


_logger = logging.getLogger(__name__)

# Transactions
tr_Modeled_Domain = "Modeled Domain"

class Domain:
    """
    Populate all relevant Domain relvars
    """
    subsystem_counter = {}
    types = None

    @classmethod
    def populate(cls, mmdb: str, domain: str, content: Dict):
        """
        Insert all user model elements in this Domain into the corresponding Metamodel classes.

        :param mmdb:  The metamodel db name
        :param domain:  The name of the domain extracted from the content
        :param content:  The parsed content of the domain
        """
        _logger.info(f"Populating modeled domain [{domain}]")
        _logger.info(f"Transaction open: domain and subsystems [{domain}]")
        Transaction.open(mmdb, tr_Modeled_Domain)

        Relvar.insert(mmdb, tr=tr_Modeled_Domain, relvar='Domain', tuples=[
            Domain_i(Name=domain, Alias=content['alias']),
        ])
        # TODO: For now assume this is always a modeled domain, but need a way to specify a realized domain
        Relvar.insert(mmdb, tr=tr_Modeled_Domain, relvar='Modeled_Domain', tuples=[
            Modeled_Domain_i(Name=domain),
            ])
        for subsys_parse in content['subsystems'].values():
            subsys = subsys_parse['class_model'].subsystem
            Relvar.insert(mmdb, tr=tr_Modeled_Domain, relvar='Subsystem', tuples=[
                Subsystem_i(Name=subsys['name'], First_element_number=subsys['range'][0],
                            Domain=domain, Alias=subsys['alias']),
            ])
            Relvar.insert(mmdb, tr=tr_Modeled_Domain, relvar='Domain_Partition', tuples=[
                Domain_Partition_i(Number=subsys['range'][0], Domain=domain)
            ])
        Transaction.execute(mmdb, tr_Modeled_Domain)
        _logger.info(f"Transaction closed: domain and subsystems [{domain}]")

        # Process all subsystem elements
        for subsys_parse in content['subsystems'].values():
            subsys = Subsystem(subsys_parse=subsys_parse['class_model'].subsystem)
            _logger.info("Populating classes")

            # Insert classes
            for c in subsys_parse['class_model'].classes:
                MMclass.populate(mmdb, domain=domain, subsystem=subsys, record=c)
            _logger.info("Populating relationships")
            for r in subsys_parse['class_model'].rels:
                Relationship.populate(mmdb, domain=domain, subsystem=subsys, record=r)

            # Insert methods
            _logger.info("Populating methods")
            for m_parse in subsys_parse['methods'].values():
                # All classes must be populated first, so that parameter types in signatures can be resolved
                # as class or non-class types
                Method.populate(mmdb, domain=domain, subsys=subsys.name, m_parse=m_parse)

            # Insert external entities and operations
            _logger.info("Populating operations")
            for ee_name, op_parse in subsys_parse['external'].items():
                EE.populate(mmdb, ee_name=ee_name, subsys=subsys.name,
                            domain=domain, op_parse=op_parse)

            # Insert state machines
            _logger.info("Populating state models")
            for sm in subsys_parse['state_models'].values():
                StateModel.populate(mmdb, subsys=subsys.name, sm=sm)

        Attribute.ResolveAttrTypes(mmdb, domain=domain)
        _logger.info("Populating lineage")
        #
        # Reprinting these for lineage debugging purposes
        Lineage.Derive(mmdb, domain=domain)
        #
        # Print out the populated metamodel
        Relvar.printall(mmdb)
        #
        # Populate actions for all Activities
        Activity.process_execution_units(mmdb)
        pass
        #
