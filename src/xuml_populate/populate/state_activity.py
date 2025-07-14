"""
state_activity.py – Populates a State's activity
"""
# System
import logging

# Model Integration
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from pyral.relation import Relation  # For debugging
from scrall.parse.parser import ScrallParser

# xUML Populate
from xuml_populate.populate.xunit import ExecutionUnit
from xuml_populate.config import mmdb
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.signature import Signature
from xuml_populate.populate.activity import Activity
from xuml_populate.populate.mm_type import MMtype
from xuml_populate.populate.mmclass_nt import (Method_Signature_i, Method_i, Parameter_i)
from xuml_populate.populate.actions.aparse_types import ActivityAP, StateActivityAP

_logger = logging.getLogger(__name__)

# Transactions
tr_Method = "Method"
tr_Parameter = "Parameter"
tr_OutputFlow = "OutputFlow"


class StateActivity:
    """
    """
    def __init__(self, state_name: str, activity_data):
        """
        Populate a State's Activity

        Args:
            state_name: Name of the state
            activity_data:
        """
        self.domain = domain
        self.subsys = subsys
        self.method_parse = m_parse
        self.xi_flow = None
        self.class_name = m_parse.class_name
        self.signum = None
        self.anum = None
        self.name = self.method_parse.method
        self.xi_flow_id = None
        self.path = f"{domain}:{self.class_name}:{self.name}.mtd"
        self.activity_detail = None

        Transaction.open(db=mmdb, name=tr_Method)
        _logger.info("Transaction open: Populating method")

        # Create the Method Signature
        self.signum = Signature.populate(tr=tr_Method, subsys=self.subsys, domain=self.domain)
        Relvar.insert(db=mmdb, tr=tr_Method, relvar='Method Signature', tuples=[
            Method_Signature_i(SIGnum=self.signum, Method=self.name, Class=self.class_name,
                               Domain=self.domain)
        ])

        # Parse the scrall and save for later population
        self.activity_parse = ScrallParser.parse_text(scrall_text=self.method_parse.activity, debug=False)

        # Populate the method
        self.anum = Activity.populate(tr=tr_Method, action_text=self.activity_parse,
                                      subsys=subsys, domain=self.domain, synchronous=True)

        # Populate the executing instance (self) flow
        self.xi_flow = Flow.populate_instance_flow(cname=self.class_name, anum=self.anum, domain=self.domain,
                                                   label='me', single=True, activity_tr=tr_Method)
        _logger.info(f"INSERT Instance Flow (method me): [{self.domain}:{self.class_name}:{self.name}:"
                     f"{self.xi_flow.fid}]")
        Relvar.insert(db=mmdb, tr=tr_Method, relvar='Method', tuples=[
            Method_i(Anum=self.anum, Name=self.name, Class=self.class_name, Domain=self.domain,
                     Executing_instance_flow=self.xi_flow.fid)
        ])

        Transaction.execute(db=mmdb, name=tr_Method)  # Populate empty method
        _logger.info("Transaction closed: Populating method")

        # Add input flows (parameters)
        for p in self.method_parse.flows_in:
            # Populate the Parameter's type if it hasn't already been populated
            MMtype.populate_unknown(name=p['type'], domain=self.domain)

            _logger.info("Transaction open: Populating method parameter")
            Transaction.open(db=mmdb, name=tr_Parameter)

            input_fid = Flow.populate_data_flow_by_type(
                mm_type=p['type'], anum=self.anum, domain=self.domain,
                label=p['name'], activity_tr=tr_Parameter).fid

            _logger.info(f"INSERT Scalar Flow (method input): ["
                         f"{self.domain}:{self.class_name}:{self.name}:^{p['name']}:{input_fid}]")
            Relvar.insert(db=mmdb, tr=tr_Parameter, relvar='Parameter', tuples=[
                Parameter_i(Name=p['name'], Signature=self.signum, Domain=self.domain,
                            Input_flow=input_fid, Activity=self.anum, Type=p['type'])
            ])
            Transaction.execute(db=mmdb, name=tr_Parameter)  # Method parameter
            _logger.info("Transaction closed: Populating parameter")

        # Output flow (created by output flow action when it is populated)

    def process_execution_units(self):
        """
        Process each Scrall Execution Unit for all Activities (Method, State, and Synchronous Operation)
        """
        _logger.info(f"Populating method execution units: {self.path}")
        # Look up signature
        R = f"Method:<{self.name}>, Class:<{self.class_name}>, Domain:<{self.domain}>"
        method_sig_r = Relation.restrict(db=mmdb, relation='Method Signature', restriction=R)
        if not method_sig_r.body:
            # TODO: raise exception here
            pass
        self.signum = method_sig_r.body[0]['SIGnum']

        # Look up xi flow
        R = f"Name:<{self.name}>, Class:<{self.class_name}>, Domain:<{self.domain}>"
        method_r = Relation.restrict(db=mmdb, relation='Method', restriction=R)
        if not method_r.body:
            # TODO: raise exception here
            pass
        self.xi_flow_id = method_r.body[0]['Executing_instance_flow']

        self.activity_detail = MethodActivityAP(anum=self.anum, domain=self.domain,
                                           cname=self.class_name, opname=self.name, xiflow=self.xi_flow_id,
                                           activity_path=self.path, scrall_text=self.activity_parse[1])

        # Here we process each statement set in the Method (Activity)
        for count, xunit in enumerate(self.activity_parse[0]):  # Use count for debugging
            c = count + 1
            if type(xunit.statement_set.statement).__name__ == 'Output_Flow_a':
                # This is the statement set that returns the Method's value
                ExecutionUnit.process_synch_output(activity_data=self.activity_detail,
                                                   synch_output=xunit.statement_set.statement)
            else:
                # This is a statement set that does not return the Method's value
                boundary_actions = ExecutionUnit.process_method_statement_set(
                    activity_data=self.activity_detail, statement_set=xunit.statement_set)

        a = Activity(name=self.name, class_name=self.class_name, activity_data=self.activity_detail)
        a.pop_flow_dependencies()
        a.assign_waves()
        a.populate_waves()
        pass

