"""
ns_flow.py – Process a Non Scalar Flow
"""

import logging
from pyral.relvar import Relvar
from pyral.relation import Relation
from typing import TYPE_CHECKING, Optional, List
from xuml_populate.exceptions.action_exceptions import FlowException
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content
from xuml_populate.populate.mm_class import MMclass
from xuml_populate.populate.actions.table import Table

if TYPE_CHECKING:
    from tkinter import Tk


# TODO: Add Table and Control Flow population

class NonScalarFlow:
    """
    Support queries common to Instance and Table Flows
    """
    _logger = logging.getLogger(__name__)

    domain = None
    activity = None
    label = None
    mmdb = None

    @classmethod
    def headers_disjoint(cls, mmdb: 'Tk', a_flow: Flow_ap, b_flow: Flow_ap, domain: str) -> bool:
        """
        Ensure that there are no common attributes shared by more than on header

        :param mmdb:
        :param a_flow:  A input
        :param b_flow:  B input
        :param domain:
        :return: True if A and B inputs are disjoint
        """
        # Create a list of headers, one per ns_flow
        headers = []
        for f in [a_flow, b_flow]:
            if f.content == Content.INSTANCE:
                hdict = MMclass.header(mmdb, cname=f.tname, domain=domain)
            else:
                hdict = Table.header(mmdb, tname=f.tname, domain=domain)
                pass
        # Convert headers from a list of dictionaries to a list of tuples
        headers = [(tuple(a.items())) for a in headers]
        # Check to see that the a and b headers in the list are disjoint
        return set(headers[0]).isdisjoint(headers[1])

    @classmethod
    def same_headers(cls, mmdb: 'Tk', a_flow: Flow_ap, b_flow: Flow_ap, domain: str) -> bool:
        """
        Ensure that each ns_flow shares the same headers

        :param mmdb:
        :param b_flow:
        :param a_flow:
        :param domain:
        :return: True if all headers share the same set of attr/type pairs
        """
        # Create a list of headers, one per ns_flow
        headers = []
        for f in [a_flow, b_flow]:
            if f.content == Content.INSTANCE:
                headers.append(MMclass.header(mmdb, cname=f.tname, domain=domain))
            else:
                headers.append(Table.header(mmdb, tname=f.tname, domain=domain))

        # We need to freeze the list before we can do a set operation on it
        # Convert headers from a list of dictionaries to a list of tuples to a tuple of tuples
        headers = tuple([(tuple(a.items())) for a in headers])
        # If all headers are the same, there will be only one set element
        return len(set(headers)) == 1
