"""
element.py – Populate an element instance in PyRAL
"""

import logging
from PyRAL.relvar import Relvar
from typing import TYPE_CHECKING
from class_model_dsl.populate.pop_types import Element_i, Spanning_Element_i, Subsystem_Element_i
# TODO: Add spanning element support

if TYPE_CHECKING:
    from tkinter import Tk

_signum_counters = {} # A separate counter per domain

class Element:
    """
    Create a State Model relation
    """
    _logger = logging.getLogger(__name__)
    _num_counters = {}  # A separate number counter per domain

    @classmethod
    def init_counter(cls, key: str) -> int:
        """
        Create a new counter using the supplied key if it does not already exist in the num counter dict

        :param key: Usually the domain name but could be subsystem_name:domain_name or something else
        :return: The next available number
        """
        # Should refactor this into an Element population numbering method
        if key not in cls._num_counters:
            cls._num_counters[key] = 1
        else:
            cls._num_counters[key] += 1
        return cls._num_counters[key]

    @classmethod
    def populate_unlabeled_subsys_element(cls, mmdb: 'Tk', prefix: str, subsystem_name: str, domain_name: str) -> str:
        """
        Generates a label for a new Subsystem Element and populates it

        :param mmdb: The Metamodel DB
        :param prefix: Prefixed to counter to create unique string label
        :param subsystem_name: The name of the subsystem since these are Subsystem Elements
        :param domain_name: The element belongs to this domain
        :return: generated label such as SIG12, A47, etc
        """

        label = f'{prefix}{cls.init_counter(key=domain_name)}'
        Relvar.insert(relvar='Element', tuples=[
            Element_i(Label=label, Domain=domain_name)
        ])
        Relvar.insert(relvar='Subsystem_Element', tuples=[
            Subsystem_Element_i(Label=label, Domain=domain_name, Subsystem=subsystem_name)
        ])
        return label

    @classmethod
    def populate_labeled_subys_element(cls, mmdb: 'Tk', label: str, subsystem_name: str, domain_name: str):
        """
        Populates pre-labeled Subsystem Element such as cnum and rnum

        Rnums are typically specified and remembered by the user directly in the xcm files
        (or in whatever tool they are using to specify a class model as they develop).

        Most users ignore the Cnums so they can be generated behind the scenes and kept as an internal labeling
        system for the most part. They are not specified in the xcm files for now (but may be later)
        :param mmdb: The Metamodel DB
        :param label: The user or generated label such as R812 for rnums or C7 for cnums
        :param subsystem_name: The name of the subsystem since these are Subsystem Elements
        :param domain_name: The element belongs to this domain
        """

        # We don't need to use our counter since the label has already been specified
        # so we just insert the Element and Subystem Element classes of the Domain Subsystem
        Relvar.insert(relvar='Element', tuples=[
            Element_i(Label=label, Domain=domain_name)
        ])
        Relvar.insert(relvar='Subsystem_Element', tuples=[
            Subsystem_Element_i(Label=label, Domain=domain_name, Subsystem=subsystem_name)
        ])