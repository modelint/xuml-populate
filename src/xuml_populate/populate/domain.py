"""
domain.py – Process parsed domain to populate the metamodel db
"""

# System
import logging
from typing import Dict
from contextlib import redirect_stdout  # For diagnostics

# Model Integration
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from pyral.relvar import Relation  # For debugging

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Method_Output_Type
from xuml_populate.populate.attribute import Attribute
from xuml_populate.populate.mm_class import MMclass
from xuml_populate.populate.method import Method
from xuml_populate.populate.relationship import Relationship
from xuml_populate.populate.lineage import Lineage
from xuml_populate.populate.subsystem import Subsystem
from xuml_populate.populate.state_model import StateModel
from xuml_populate.populate.ee import EE
from xuml_populate.populate.mmclass_nt import Domain_i, Modeled_Domain_i, Domain_Partition_i, Subsystem_i

if __debug__:
    from xuml_populate.utility import print_mmdb

_logger = logging.getLogger(__name__)

# Transactions
tr_Modeled_Domain = "Modeled Domain"

class Domain:
    """
    Populate all relevant Domain relvars
    """
    def __init__(self, domain: str, content: Dict, parse_actions: bool, verbose: bool):
        """
        Insert all user model elements in this Domain into the corresponding Metamodel classes.

        :param domain:  The name of the domain extracted from the content
        :param content:  The parsed content of the domain
        """
        _logger.info(f"Populating modeled domain [{domain}]")

        self.name = domain
        self.subsystem_counter = {}
        self.types = None
        self.parse_actions = parse_actions
        self.methods: dict[str, Method] = {}  # Methods keyed by activity number
        self.state_models = []

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

            # Insert methods
            _logger.info("Populating methods")
            for m_parse in subsys_parse['methods'].values():
                # All classes must be populated first, so that parameter types in signatures can be resolved
                # as class or non-class types
                m = Method(domain=self.name, subsys=subsys.name, m_parse=m_parse, parse_actions=parse_actions)
                self.methods[m.anum] = m

            # Insert state models
            _logger.info("Populating state models")
            for sm in subsys_parse['state_models'].values():
                pop_sm = StateModel(subsys=subsys.name, sm=sm, parse_actions=self.parse_actions)
                self.state_models.append(pop_sm)

        _logger.info("Resolving attribute types")
        Attribute.ResolveAttrTypes(domain=domain)

        _logger.info("Populating lineage")
        Lineage.Derive(domain=domain)

        # Populate actions for all Activities

        # For Methods, we must populate activities in two passes

        # This is because a Method might call some other Method using a Method Call Action
        # But we can't complete our population of the Method Call Action beause it populates a relationship
        # to Synchronous Output for a possibly unpopulated Method.

        # The Method Call Action also need to know the output type of its target Method so that it can populate
        # output Data Flows.

        # Fortunately, we gathered the signature data when we populated the Method (minus actions) earlier.
        # Here we assemble the output types into a dictionary that we can use while populating any Method
        # Call Actions to populate any target Method output flows.

        method_output_types = {
            anum: Method_Output_Type(name=m.method_parse.flow_out, mult=m.method_parse.mult_out)
            for anum, m in self.methods.items()
        }

        # Populate all external entities and services
        for ee, services in content['external']['External Entities'].items():
            events = services.get('external events', [])
            ops = services.get('external operations', [])
            if events or ops:
                # Open a new EE transaction and insert the EE instance
                EE.populate(name=ee, domain=self.name)
            else:
                # EE doesn't serve any function, so we skip it
                # We should probably log it as a warning as well
                continue
            for e in events:
                pass
            pass

        # First pass: Method action population
        # Here we populate everything except the Method Call Action parameter inputs
        # Note that we inject the method output types
        for anum, m in self.methods.items():
            m.process_execution_units(method_output_types=method_output_types)

        # Second pass: Compute any Method Call population
        for anum, m in self.methods.items():
            m.post_process()

        for s in self.state_models:
            s.process_states(method_output_types=method_output_types)

        pass

        # Print out the populated metamodel
        if verbose:
            Relvar.printall(mmdb)
        #
