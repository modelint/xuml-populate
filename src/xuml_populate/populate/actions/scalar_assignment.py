"""
scalar_assignment.py – Populate elements of a scalar assignment
"""
# System
import logging
from typing import TYPE_CHECKING
from collections import namedtuple

# Model Integration
from scrall.parse.visitor import Scalar_Assignment_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.config import mmdb
from xuml_populate.populate.mmclass_nt import Labeled_Flow_i
from xuml_populate.populate.actions.extract_action import ExtractAction
from xuml_populate.populate.ns_flow import NonScalarFlow
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.aparse_types import ( Flow_ap, MaxMult, Content, SMType,
                                                          Boundary_Actions, ActivityType )
from xuml_populate.populate.actions.expressions.scalar_expr import ScalarExpr
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.actions.write_action import WriteAction
if __debug__:
    from xuml_populate.utility import print_mmdb

_logger = logging.getLogger(__name__)

# Transactions
tr_Migrate = "Migrate to Label"

class ScalarAssignment:
    """
    Break down a scalar assignment statement into action semantics and populate them
    """

    def __init__(self, activity: 'Activity', scalar_assign_parse: Scalar_Assignment_a):
        """

        Args:
            activity: The enclosing activity object
            scalar_assign_parse: A parsed scalar assignment

        Returns
            a list of scalar flows
        """
        self.scalar_assign_parse = scalar_assign_parse
        self.activity = activity
        self.input_instance_flow = None  # The instance flow feeding the next component on the RHS
        self.input_instance_ctype = None  # The class type of the input instance flow
        self.domain = self.activity.domain
        self.anum = self.activity.anum
        self.activity_path = activity.activity_path
        self.scrall_text = activity.scrall_text

        self.initial_actions: set[str] = set()  # Actions that initiate some RHS expression
        self.final_actions: set[str] = set()  # Actions that terminate some RHS expression
        self.input_flows: list[Flow_ap] = []  # Left to right sequence of input flows passing output to the LHS

    def process(self) -> Boundary_Actions:
        """
        Given a parsed scalar assignment consisting of an LHS and an RHS, populate each component action
        and return the boundary actions.

        We'll need an initial_pseudo_state flow and we'll need to create intermediate instance flows to connect the components.
        The final output flow must be a scalar flow. The associated Scalar determines the type of the
        assignment.

        Returns:
            boundary actions
        """
        # Split of the left and right and sides of the assignment
        lhs = self.scalar_assign_parse.lhs
        rhs = self.scalar_assign_parse.rhs

        # Set the executing or partitioning instance flow
        if self.activity.atype == ActivityType.STATE:
            match self.activity.smtype:
                case SMType.LIFECYCLE:
                    self.input_instance_flow = self.activity.xiflow
                case SMType.MA:
                    self.input_instance_flow = self.activity.piflow
                case SMType.SA:
                    # A single assigner state machine has no executing instance and hence no xi_flow
                    pass
        elif self.activity.atype == ActivityType.METHOD:
            self.input_instance_flow = self.activity.xiflow
        else:
            raise ActionException

        # If there are two labeled flows on the LHS receiving the result of a boolean expression
        # We need a Boolean Partition computation action
        boolean_partition = True if len(lhs) == 2 and len(rhs) == 1 and type(rhs[0]).__name__ == 'BOOL_a' else False

        # There may be multiple expressions, each producing one or more scalar flows on the RHS
        # We will later ensure that there are an equal number of flow outputs on the LHS so they match up
        for rhs_expr in rhs:
            se = ScalarExpr(expr=rhs_expr, input_instance_flow=self.input_instance_flow, activity=self.activity,
                            bpart=boolean_partition)
            bactions, scalar_flows = se.process()
            self.input_flows.extend(scalar_flows)
            self.initial_actions.update(bactions.ain)
            self.final_actions.update(bactions.aout)

            # Where any actions populated for the RHS?
            if not bactions.ain and not bactions.aout:
                # There is always at least one Scalar Flow emanating from the RHS, but there is a case where
                # the Scalar Flow isn't produced by any Action. And that happens when the value is explicitly written
                # into the action language. We call this a Scalar Value (you can think of it as a constant) like
                # TRUE, FALSE, or an enum value like _up or _down.
                # For example: Stop requested = TRUE
                if not scalar_flows:
                    # It's not an assigment if there is nothing to assign!
                    msg = f"No flow to assign in Scalar Assigment in: {self.activity.activity_path}"
                    _logger.error(msg)
                    raise ActionException(msg)

        # Now we deal with the LHS expressions
        # Each is an output to either an attribute write action or a labeled flow

        # If we output to a write action, there can only be (for now) a single attribute write destination
        # Which means we can have only one RHS output flow

        # Write to an attribute
        if type(lhs[0]).__name__ == 'Qualified_Name_a':
            if len(lhs) > 1:
                msg = (f"Scalar expr writing to an attribute has more than one LHS output in scalar assignment"
                       f" at {self.activity.activity_path}")
                _logger.error(msg)
                raise ActionException(msg)
            if len(rhs) != 1:
                msg = (f"Scalar expr writing to an attribute requires one RHS input in scalar assignment"
                       f" at {self.activity.activity_path}")
                _logger.error(msg)
                raise ActionException(msg)
            attr_name = lhs[0].aname  # We are writing to this attribute
            qname_iset = lhs[0].iset  # Might be qualified by an iset expression /R4/R7/Cursor.X, for example
            if qname_iset:
                # TODO: Need to handle iset as qualifier in attribute write destination
                msg = (f"Under construction - Need to handle iset as qualifier in attribute write destination"
                       f" at {self.activity.activity_path}")
                _logger.error(msg)
                raise IncompleteActionException(msg)
            else:
                # Qualified by a labeled single instance flow with the target instance of the attribute write action
                si_flow_label = lhs[0].cname  # unfortunate choice of field name, its not a class name
                # There must be a labeled flow
                si_flows = Flow.find_labeled_ns_flow(name=si_flow_label, anum=self.anum, domain=self.domain)
                if len(si_flows) != 1:
                    msg = (f"Input to attribute write action in scalar assignment must be a single scalar flow"
                           f" at {self.activity.activity_path}")
                    _logger.error(msg)
                    raise ActionException(msg)
                target_si_flow = si_flows[0]
                rhs_input = self.input_flows[0]
                wa = WriteAction(write_to_instance_flow=target_si_flow, value_to_write_flow=rhs_input,
                                 attr_name=attr_name, activity=self.activity)
                write_aid = wa.populate()  # returns the write action id (not used)

                self.final_actions = {write_aid}
                self.initial_actions = {write_aid} if not self.initial_actions else self.initial_actions

                bactions = Boundary_Actions(ain=self.initial_actions, aout=self.final_actions)
                return bactions

        # Pass input from one or more RHS flows to one or more labeled LHS flows
        lhs_outputs = []
        scalar_flow_labels = [n.name.name for n in lhs]

        # There must be a label on the LHS for each scalar output flow
        if len(self.input_flows) != len(scalar_flow_labels):
            _logger.error(f"LHS provides {len(scalar_flow_labels)} labels, but RHS outputs {len(self.input_flows)} flows")
            raise ScalarAssignmentFlowMismatch

        # TODO: For each LHS label that explicity specifies a type, verify match with corresponding attribute in flow

        # Now we need to convert the unlabeled non scalar output_flow into one labeled scalar flow per
        # attribute in the output flow header
        # TODO: handle case where lhs is an explicit table assignment
        # Since this is a scalar flow, we need to verify that the output flow is either a single instance or tuple
        # flow with the same number of attributes as the LHS. For now let's ignore explicit typing on the LHS
        # but we need to check that later.
        writing_to_attribute = False  # We use this later when registering the output label
        for count, label in enumerate(scalar_flow_labels):
            # Get the corresponding input_flow and actions
            rhs_input = self.input_flows[count]
            # If the label is the unqualified name of an attribute of the executing instance, we need to write
            # to that attribute and in this case, there is no need for a Labeled Flow
            class_name = None

            if self.activity.atype == ActivityType.STATE and self.activity.smtype == SMType.LIFECYCLE:
                class_name = self.activity.state_model
            elif self.activity.atype == ActivityType.METHOD:
                class_name = self.activity.class_name
            if class_name:
                R = f"Name:<{label}>, Class:<{class_name}>, Domain:<{self.activity.domain}>"
                attribute_r = Relation.restrict(db=mmdb, relation="Attribute", restriction=R)
                if attribute_r.body:
                    writing_to_attribute = True
                    wa = WriteAction(write_to_instance_flow=self.input_instance_flow,
                                     value_to_write_flow=rhs_input,
                                     attr_name=label, activity=self.activity)
                    write_aid = wa.populate()  # returns the write action id (not used)
                    # Since the write action is on the lhs it is the one and only final boundary action
                    # So we replace whatever action ids might have been assigned to the set
                    self.final_actions = {write_aid}
                    self.initial_actions = {write_aid} if not self.initial_actions else self.initial_actions
                    continue

            # Relabel or migrate sflow to a labeled flow matching the LHS flow name
            pre_labeled_sflow = Flow.lookup_label(fid=rhs_input.fid, anum=self.anum, domain=self.domain)
            if pre_labeled_sflow:
                Flow.relabel_flow(new_label=label, fid=rhs_input.fid, anum=self.anum, domain=self.domain)
            else:
                # Migrate the scalar_flow to a labeled flow
                Flow.label_flow(label=label, fid=rhs_input.fid, anum=self.anum, domain=self.domain)

        if not writing_to_attribute and self.final_actions:
            pass
            # TODO: Figure out what we need down here
            # If we aren't writing an attr value and an action generated the output scalar
            # we register the output
            for f in self.input_flows:
                # Ensure there is exacly one source action id
                if len(self.final_actions) != 1:
                    msg = (f"Expected only one action id as input to flow in scalar assignment for"
                           f"LHS {lhs} in: {self.activity.activity_path}")
                    _logger.error(msg)
                    raise ActionException(msg)
                # Use comma to extract one element from the set
                self.activity.labeled_outputs[f.fid], = self.final_actions

        return Boundary_Actions(ain=self.initial_actions, aout=self.final_actions)
