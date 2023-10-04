"""
ns_flow.py – Process a Non Scalar Flow
"""

import logging
from xuml_populate.config import mmdb
from pyral.relation import Relation
from typing import Optional, List, Dict
from xuml_populate.exceptions.action_exceptions import FlowException, NonScalarFlowRequired
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content
from xuml_populate.populate.mm_class import MMclass
from xuml_populate.populate.actions.table import Table

# TODO: Add Table and Control Flow population

_logger = logging.getLogger(__name__)


class NonScalarFlow:
    """
    Support queries common to Instance and Table Flows
    """

    domain = None
    activity = None
    label = None

    @classmethod
    def header_union(cls, a_flow: Flow_ap, b_flow: Flow_ap, domain: str) -> Dict[str, str]:
        # Create a list of headers, one per ns_flow
        headers = []
        for f in [a_flow, b_flow]:
            if f.content == Content.INSTANCE:
                headers.append(MMclass.header(cname=f.tname, domain=domain))
            else:
                headers.append(Table.header(tname=f.tname, domain=domain))
        # Convert the two headers from a list of dictionaries to a pair of tuples
        h = [(tuple(h.items())) for h in headers]
        # Union is formed by stepping through each attribute and adding it to a set
        u = {e for i in h for e in i}
        # Now convert back to a dictionary
        return {t[0]: t[1] for t in u}

    @classmethod
    def header(cls, ns_flow: Flow_ap, domain:str) -> Dict[str, str]:
        """
        Given a Non Scalar Flow, obtain its header

        :param ns_flow:
        :param domain:
        :return: Header as a dictionary of attr:scalar (type) pairs
        """
        match ns_flow.content:
            case Content.INSTANCE:
                return MMclass.header(ns_flow.tname, domain)
            case Content.RELATION:
                return Table.header(ns_flow.tname, domain)
            case _:
                raise NonScalarFlowRequired

    @classmethod
    def headers_disjoint(cls, a_flow: Flow_ap, b_flow: Flow_ap, domain: str) -> bool:
        """
        Ensure that there are no common attributes shared by more than on header

        :param a_flow:  A input
        :param b_flow:  B input
        :param domain: The domain name
        :return: True if A and B inputs are disjoint
        """
        # Create a list of headers, one per ns_flow
        headers = []
        for f in [a_flow, b_flow]:
            if f.content == Content.INSTANCE:
                headers.append(MMclass.header(cname=f.tname, domain=domain))
            else:
                headers.append(Table.header(tname=f.tname, domain=domain))
        # Convert the two headers from a list of dictionaries to a pair of tuples
        a_header, b_header = [(tuple(h.items())) for h in headers]
        # Check to see that the a and b headers in the list are disjoint
        return set(a_header).isdisjoint(b_header)

    @classmethod
    def same_headers(cls, a_flow: Flow_ap, b_flow: Flow_ap, domain: str) -> bool:
        """
        Ensure that each ns_flow shares the same headers

        :param a_flow:
        :param b_flow:
        :param domain:
        :return: True if all headers share the same set of attr/type pairs
        """
        # Create a list of headers, one per ns_flow
        headers = []
        for f in [a_flow, b_flow]:
            if f.content == Content.INSTANCE:
                headers.append(MMclass.header(cname=f.tname, domain=domain))
            else:
                headers.append(Table.header(tname=f.tname, domain=domain))

        # We need to freeze the list before we can do a set operation on it
        # Convert headers from a list of dictionaries to a list of tuples to a tuple of tuples
        headers = tuple([(tuple(a.items())) for a in headers])
        # If all headers are the same, there will be only one set element
        return len(set(headers)) == 1
