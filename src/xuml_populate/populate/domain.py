"""
domain.py – Process parsed domain to populate the metamodel db
"""

# System
import logging
from typing import Dict

# Model Integration
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from pyral.relvar import Relation  # For debugging

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.attribute import Attribute
from xuml_populate.populate.mm_class import MMclass
from xuml_populate.populate.method import Method
from xuml_populate.populate.relationship import Relationship
from xuml_populate.populate.ee import EE
from xuml_populate.populate.lineage import Lineage
from xuml_populate.populate.subsystem import Subsystem
from xuml_populate.populate.state_model import StateModel
from xuml_populate.populate.activity import Activity
from xuml_populate.populate.mmclass_nt import Domain_i, Modeled_Domain_i, Domain_Partition_i, Subsystem_i


_logger = logging.getLogger(__name__)

# Transactions
tr_Modeled_Domain = "Modeled Domain"

class Domain:
    """
    Populate all relevant Domain relvars
    """
    def __init__(self, domain: str, content: Dict, parse_actions: bool, display=False):
        """
        Insert all user model elements in this Domain into the corresponding Metamodel classes.

        :param domain:  The name of the domain extracted from the content
        :param content:  The parsed content of the domain
        """
        _logger.info(f"Populating modeled domain [{domain}]")

        self.subsystem_counter = {}
        self.types = None
        self.parse_actions = parse_actions

        _logger.info(f"Transaction open: domain and subsystems [{domain}]")
        Transaction.open(db=mmdb, name=tr_Modeled_Domain)

        Relvar.insert(db=mmdb, tr=tr_Modeled_Domain, relvar='Domain', tuples=[
            Domain_i(Name=domain, Alias=content['alias']),
        ])
        # TODO: For now assume this is always a modeled domain, but need a way to specify a realized domain
        Relvar.insert(db=mmdb, tr=tr_Modeled_Domain, relvar='Modeled_Domain', tuples=[
            Modeled_Domain_i(Name=domain),
            ])
        for subsys_parse in content['subsystems'].values():
            subsys = subsys_parse['class_model'].subsystem
            Relvar.insert(db=mmdb, tr=tr_Modeled_Domain, relvar='Subsystem', tuples=[
                Subsystem_i(Name=subsys['name'], First_element_number=subsys['range'][0],
                            Domain=domain, Alias=subsys['alias']),
            ])
            Relvar.insert(db=mmdb, tr=tr_Modeled_Domain, relvar='Domain_Partition', tuples=[
                Domain_Partition_i(Number=subsys['range'][0], Domain=domain)
            ])
        Transaction.execute(db=mmdb, name=tr_Modeled_Domain)
        _logger.info(f"Transaction closed: domain and subsystems [{domain}]")

        # Process all subsystem elements
        for subsys_parse in content['subsystems'].values():
            subsys = Subsystem(subsys_parse=subsys_parse['class_model'].subsystem)
            _logger.info("Populating classes")

            # Insert classes
            for c in subsys_parse['class_model'].classes:
                MMclass.populate(domain=domain, subsystem=subsys, record=c)
            _logger.info("Populating relationships")
            for r in subsys_parse['class_model'].rels:
                Relationship.populate(domain=domain, subsystem=subsys, record=r)

            # Insert external entities and operations
            _logger.info("Populating operations")
            for ee_name, op_parse in subsys_parse['external'].items():
                EE.populate(ee_name=ee_name, subsys=subsys.name,
                            domain=domain, op_parse=op_parse)

            # Relvar.printall(mmdb)
            # Insert methods
            _logger.info("Populating methods")
            for m_parse in subsys_parse['methods'].values():
                # All classes must be populated first, so that parameter types in signatures can be resolved
                # as class or non-class types
                Method(domain=domain, subsys=subsys.name, m_parse=m_parse, parse_actions=parse_actions)

            # Insert state machines
            _logger.info("Populating state models")
            for sm in subsys_parse['state_models'].values():
                StateModel(subsys=subsys.name, sm=sm, parse_actions=self.parse_actions)

        Attribute.ResolveAttrTypes(domain=domain)
        _logger.info("Populating lineage")
        #
        # Reprinting these for lineage debugging purposes
        Lineage.Derive(domain=domain)
        #
        # Print out the populated metamodel
        if display:
            Relvar.printall(mmdb)
        #
        # Populate actions for all Activities
        Activity.process_execution_units()  # TODO: For now, only methods
        # if self.parse_actions:
        #     Activity.process_execution_units()
        pass
        #
