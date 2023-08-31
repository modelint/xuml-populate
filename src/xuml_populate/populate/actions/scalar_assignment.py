"""
scalar_assignment.py – Populate elements of a scalar assignment
"""

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from xuml_populate.populate.mmclass_nt import Labeled_Flow_i
from xuml_populate.populate.actions.extract_action import ExtractAction
from xuml_populate.populate.ns_flow import NonScalarFlow
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content
from xuml_populate.populate.actions.expressions.scalar_expr import ScalarExpr
from xuml_populate.exceptions.action_exceptions import ScalarAssignmentFlowMismatch, ScalarAssignmentfromMultipleTuples

from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

from collections import namedtuple

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class ScalarAssignment:
    """
    Break down a scalar assignment statement into action semantics and populate them

    """

    input_instance_flow = None  # The instance flow feeding the next component on the RHS
    input_instance_ctype = None  # The class type of the input instance flow
    domain = None
    anum = None
    mmdb = None
    activity_path = None
    scrall_text = None

    @classmethod
    def process(cls, mmdb: 'Tk', anum: str, cname: str, domain: str, scalar_assign_parse,
                xi_flow_id: str, activity_path: str, scrall_text: str):
        """
        Given a parsed table assignment consisting of an LHS and an RHS, populate each component action
        and return the resultant table flow

        We'll need an initial flow and we'll need to create intermediate instance flows to connect the components.
        The final output flow must be a table flow. The associated Table determines the type of the
        assignment. If the LHS spcifies an explicit Table, the resultant Table which must match.

        :param mmdb: The metamodel db
        :param cname: The class (for an operation it is the proxy class)
        :param domain: In this domain
        :param anum: The Activity Number
        :param scalar_assign_parse: A parsed scalar assignment
        :param xi_flow_id: The ID of the executing instance flow (the instance executing this anum)
        :param activity_path: Human readable path to the anum for error reporting
        :param scrall_text: The parsed scrall text for error reporting
        """
        lhs = scalar_assign_parse.lhs
        rhs = scalar_assign_parse.rhs
        cls.input_instance_flow = xi_flow_id

        # The executing instance is by nature a single instance flow
        xi_instance_flow = Flow_ap(fid=xi_flow_id, content=Content.INSTANCE, tname=cname, max_mult=MaxMult.ONE)

        output_flow, attr_list = ScalarExpr.process(mmdb, rhs=rhs, anum=anum,
                                        input_instance_flow=xi_instance_flow, domain=domain,
                                        activity_path=activity_path, scrall_text=scrall_text)

        output_flow_labels = [n for n in lhs[0].name]
        of_header = NonScalarFlow.header(mmdb, ns_flow=output_flow, domain=domain)

        # Cardinality must be tuple or single instance flow
        if output_flow.max_mult != MaxMult.ONE:
            _logger.error(f"Cannot assign values since scalar expression yields multiple tuples")
            raise ScalarAssignmentfromMultipleTuples

        # There must be a label on the LHS for each scalar output flow
        if len(of_header) != len(output_flow_labels):
            _logger.error(f"LHS provides {len(of_header)} labels, but RHS outputs {len(output_flow_labels)} flows")
            raise ScalarAssignmentFlowMismatch

        # TODO: For each LHS label that explicity specifies a type, verify match with corresponding attribute in flow

        # Now we need to convert the unlabeled non scalar output_flow into one labeled scalar flow per
        # attribute in the output flow header
        # TODO: handle case where lhs is an explicit table assignment
        # Since this is a scalar flow, we need to verify that the output flow is either a single instance or tuple
        # flow with the same number of attributes as the LHS. For now let's ignore explicit typing on the LHS
        # but we need to check that later.

        # Create one Extract Action per attribute, label pair
        for count, a in enumerate(attr_list):
            ExtractAction.populate(mmdb, tuple_flow=output_flow, attr=a, target_flow_name=output_flow_labels[count],
                                   anum=anum, domain=domain, activity_path=activity_path, scrall_text=scrall_text)