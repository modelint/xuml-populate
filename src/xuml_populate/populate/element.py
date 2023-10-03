"""
element.py – Populate an element instance in PyRAL
"""

import logging
from pyral.relvar import Relvar
from xuml_populate.config import mmdb
from xuml_populate.populate.mmclass_nt import Element_i, Spanning_Element_i, Subsystem_Element_i
# TODO: Add spanning element support

_signum_counters = {}  # A separate counter per domain
_logger = logging.getLogger(__name__)

class Element:
    """
    Create a State Model relation
    """
    _num_counters = {}  # A separate number counter per domain

    @classmethod
    def init_counter(cls, key: str) -> int:
        """
        Create a new counter using the supplied key if it does not already exist in the num counter dict

        :param key: Usually the domain name but could be subsys:domain or something else
        :return: The next available number
        """
        # Should refactor this into an Element population numbering method
        if key not in cls._num_counters:
            cls._num_counters[key] = 1
        else:
            cls._num_counters[key] += 1
        return cls._num_counters[key]

    @classmethod
    def populate_unlabeled_subsys_element(cls, tr: str, prefix: str, subsystem: str, domain: str) -> str:
        """
        Generates a label for a new Subsystem Element and populates it

        :param tr:  An open transaction name
        :param prefix: Prefixed to counter to create unique string label
        :param subsystem: The name of the subsystem since these are Subsystem Elements
        :param domain: The element belongs to this domain
        :return: generated label such as SIG12, A47, etc
        """

        label = f'{prefix}{cls.init_counter(key=domain)}'
        Relvar.insert(mmdb, tr=tr, relvar='Element', tuples=[
            Element_i(Label=label, Domain=domain)
        ])
        Relvar.insert(mmdb, tr=tr, relvar='Subsystem_Element', tuples=[
            Subsystem_Element_i(Label=label, Domain=domain, Subsystem=subsystem)
        ])
        return label

    @classmethod
    def populate_labeled_subys_element(cls, tr: str, label: str, subsystem: str, domain: str):
        """
        Populates pre-labeled Subsystem Element such as cnum and rnum

        Rnums are typically specified and remembered by the user directly in the xcm files
        (or in whatever tool they are using to specify a class model as they develop).

        Most users ignore the Cnums so they can be generated behind the scenes and kept as an internal labeling
        system for the most part. They are not specified in the xcm files for now (but may be later)

        :param tr:  An open transaction name
        :param label: The user or generated label such as R812 for rnums or C7 for cnums
        :param subsystem: The name of the subsystem since these are Subsystem Elements
        :param domain: The element belongs to this domain
        """

        # We don't need to use our counter since the label has already been specified
        # so we just insert the Element and Subystem Element classes of the Domain Subsystem
        Relvar.insert(mmdb, tr=tr, relvar='Element', tuples=[
            Element_i(Label=label, Domain=domain)
        ])
        Relvar.insert(mmdb, tr=tr, relvar='Subsystem_Element', tuples=[
            Subsystem_Element_i(Label=label, Domain=domain, Subsystem=subsystem)
        ])


    @classmethod
    def depopulate_spanning_element(cls, tr: str, label: str, domain: str):
        """
        Remove the specified spanning elmenent type from the database.

        Assumes that the spanning element subclass is managing the db transaction

        :param tr:  An open transaction name
        :param label: The user or generated label such as R812 for rnums or C7 for cnums
        :param domain: The element belongs to this domain
        """
        Relvar.deleteone(mmdb, tr=tr, relvar_name='Spanning_Element', tid={'Label': label, 'Domain': domain})
        Relvar.deleteone(mmdb, tr=tr, relvar_name='Element', tid={'Label': label, 'Domain': domain})