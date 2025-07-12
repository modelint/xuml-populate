"""
scalar_assignment.py – Populate elements of a scalar assignment
"""
# System
import logging

# Model Integration
from scrall.parse.visitor import Scalar_Assignment_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML populate
from xuml_populate.config import mmdb
from xuml_populate.pop_types import SMType
from xuml_populate.populate.mmclass_nt import Labeled_Flow_i
from xuml_populate.populate.actions.extract_action import ExtractAction
from xuml_populate.populate.ns_flow import NonScalarFlow
from xuml_populate.populate.actions.aparse_types import (Flow_ap, MaxMult, Content, ActivityAP,
                                                         MethodActivityAP, StateActivityAP, Boundary_Actions)
from xuml_populate.populate.actions.expressions.scalar_expr import ScalarExpr
from xuml_populate.exceptions.action_exceptions import ScalarAssignmentFlowMismatch, ScalarAssignmentfromMultipleTuples
from xuml_populate.populate.actions.write_action import WriteAction

_logger = logging.getLogger(__name__)

# Transactions
tr_Migrate = "Migrate to Label"

class ScalarAssignment:
    """
    Break down a scalar assignment statement into action semantics and populate them
    """

    def __init__(self, activity_data: ActivityAP, scalar_assign_parse: Scalar_Assignment_a):
        """

        Args:
            activity_data:
            scalar_assign_parse: A parsed scalar assignment
        """
        self.scalar_assign_parse = scalar_assign_parse
        self.activity_data = activity_data
        self.input_instance_flow = None  # The instance flow feeding the next component on the RHS
        self.input_instance_ctype = None  # The class type of the input instance flow
        self.domain = self.activity_data.domain
        self.anum = self.activity_data.anum
        self.activity_path = activity_data.activity_path
        self.scrall_text = activity_data.scrall_text

    def process(self) -> Boundary_Actions:
        """
        Given a parsed scalar assignment consisting of an LHS and an RHS, populate each component action
        and return the boundary actions.

        We'll need an initial flow and we'll need to create intermediate instance flows to connect the components.
        The final output flow must be a scalar flow. The associated Scalar determines the type of the
        assignment.

        Returns:
            boundary actions
        """
        lhs = self.scalar_assign_parse.lhs
        rhs = self.scalar_assign_parse.rhs

        if isinstance(self.activity_data, StateActivityAP):
            match self.activity_data.smtype:
                case SMType.LIFECYCLE:
                    self.input_instance_flow = Flow_ap(fid=self.activity_data.xiflow, content=Content.INSTANCE,
                                                       tname=self.activity_data.state_model, max_mult=MaxMult.ONE)
                case SMType.MA:
                    self.input_instance_flow = Flow_ap(fid=self.activity_data.piflow, content=Content.INSTANCE,
                                                       tname=self.activity_data.pclass, max_mult=MaxMult.ONE)
                case SMType.SA:
                    # A single assigner state machine has no executing instance and hence no xi_flow
                    pass
        elif isinstance(self.activity_data, MethodActivityAP):
            self.input_instance_flow = Flow_ap(fid=self.activity_data.xiflow, content=Content.INSTANCE,
                                               tname=self.activity_data.cname, max_mult=MaxMult.ONE)

        se = ScalarExpr(rhs=rhs, input_instance_flow=self.input_instance_flow, activity_data=self.activity_data)
        bactions, scalar_flows = se.process()

        # Where any actions populated for the RHS?
        if not bactions.ain and not bactions.aout:
            # There is always at least one Scalar Flow emanating from the RHS, but there is a case where
            # the Scalar Flow isn't produced by any Action. And that happens when the value is explicitly written
            # into the action language. We call this a Scalar Value (you can think of it as a constant) like
            # TRUE, FALSE, or an enum value like _up or _down.
            # For example: Stop requested = TRUE
            if not scalar_flows:
                # It's not an assigment if there is nothing to assign!
                pass  # TODO: raise exception, the spice must flow

            # for n in lhs[0]:
            #     pass
            pass

        # Extract flow label names from the left hand side (flow names become label names)
        scalar_flow_labels = [n for n in lhs[0].name]

        # There must be a label on the LHS for each scalar output flow
        if len(scalar_flows) != len(scalar_flow_labels):
            _logger.error(f"LHS provides {len(scalar_flow_labels)} labels, but RHS outputs {len(scalar_flows)} flows")
            raise ScalarAssignmentFlowMismatch

        # TODO: For each LHS label that explicity specifies a type, verify match with corresponding attribute in flow

        # Now we need to convert the unlabeled non scalar output_flow into one labeled scalar flow per
        # attribute in the output flow header
        # TODO: handle case where lhs is an explicit table assignment
        # Since this is a scalar flow, we need to verify that the output flow is either a single instance or tuple
        # flow with the same number of attributes as the LHS. For now let's ignore explicit typing on the LHS
        # but we need to check that later.
        for count, label in enumerate(scalar_flow_labels):
            # If the label is the name of an attribute of the executing instance, we need to write to that attribute
            # and in this case, there is no need for a Labeled Flow
            # TODO: What if the LHS is an attribute of some other instance/class?  ex: left traffic light.Signal = _go
            class_name = None
            if isinstance(self.activity_data, StateActivityAP) and self.activity_data.smtype == SMType.LIFECYCLE:
                class_name = self.activity_data.state_model
            elif isinstance(self.activity_data, MethodActivityAP):
                class_name = self.activity_data.cname
            if class_name:
                R = f"Name:<{label}>, Class:<{class_name}>, Domain:<{self.activity_data.domain}>"
                attribute_r = Relation.restrict(db=mmdb, relation="Attribute", restriction=R)
                if attribute_r.body:
                    wa = WriteAction(write_to_instance_flow=self.input_instance_flow,
                                     value_to_write_flow=scalar_flows[count],
                                     attr_name=label, anum=self.activity_data.anum, domain=self.activity_data.domain)
                    write_aid = wa.populate()  # returns the write action id (not used)
                    # Since the write action is on the lhs it is the one and only final boundary action
                    # So we replace whatever action ids might have been assigned to the set
                    write_out = {write_aid}
                    old_ain = bactions.ain
                    # If the scalar expression had no actions, the initial action is also the final action
                    write_in = {write_aid} if not old_ain else old_ain
                    bactions = Boundary_Actions(ain=write_in, aout=write_out)
                    pass
                    continue
            sflow = scalar_flows[count]
            # Migrate the scalar_flow to a labeled flow
            _logger.info(f"Labeling output of scalar expression to [{lhs}]")
            Transaction.open(db=mmdb, name=tr_Migrate)
            # Delete the Unlabeled flow
            Relvar.deleteone(db=mmdb, tr=tr_Migrate, relvar_name="Unlabeled Flow",
                             tid={"ID": sflow.fid, "Activity": self.activity_data.anum, "Domain": self.activity_data.domain})
            # Insert the labeled flow
            Relvar.insert(db=mmdb, tr=tr_Migrate, relvar='Labeled Flow', tuples=[
                Labeled_Flow_i(ID=sflow.fid, Activity=self.activity_data.anum, Domain=self.activity_data.domain, Name=label)
            ])
            Transaction.execute(db=mmdb, name=tr_Migrate)
        return bactions

        # Create one Extract Action per attribute, label pair
        # for count, a in enumerate(attr_list):
        #     ExtractAction.populate(tuple_flow=output_flow, attr=a, target_flow_name=output_flow_labels[count],
        #                            anum=anum, domain=domain, activity_path=activity_path, scrall_text=scrall_text)
