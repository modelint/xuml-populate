"""
method.py – Process parsed method to populate the metamodel db
"""
# System
import logging
from typing import Optional

# Model Integration
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from pyral.relation import Relation  # For debugging
from mtd_parser.method_visitor import Method_a
from scrall.parse.parser import ScrallParser

# xUML Populate
from xuml_populate.populate.xunit import ExecutionUnit
from xuml_populate.config import mmdb
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.signature import Signature
from xuml_populate.populate.activity import Activity
from xuml_populate.populate.mm_type import MMtype
from xuml_populate.populate.actions.aparse_types import Method_Output_Type
from xuml_populate.populate.mmclass_nt import Method_Signature_i, Method_i, Parameter_i, Synchronous_Output_i
from xuml_populate.populate.actions.aparse_types import MethodActivityAP

if __debug__:
    from xuml_populate.utility import print_mmdb

_logger = logging.getLogger(__name__)

# Transactions
tr_Method = "Method"
tr_Parameter = "Parameter"
tr_OutputFlow = "OutputFlow"

class Method:
    """
    Populate all relevant Method relvars
    """
    def __init__(self, domain: str, subsys: str, m_parse: Method_a, parse_actions: bool):
        """
        Populate a Method

        Args:
            domain: The name of the domain
            subsys: The name of the subsystem
            m_parse: The parsed content of the method
            parse_actions:
        """
        self.domain = domain
        self.subsys = subsys
        self.method_parse = m_parse
        self.class_name = m_parse.class_name
        self.signum = None
        self.anum = None
        self.name = self.method_parse.method
        self.xi_flow_id = None
        self.xi_flow = None
        self.path = f"{domain}:{self.class_name}.{self.name}"
        self.activity_obj: Optional[Activity] = None

        Transaction.open(db=mmdb, name=tr_Method)
        _logger.info("Transaction open: Populating method")

        # Create the Method Signature
        self.signum = Signature.populate(tr=tr_Method, domain=self.domain)
        Relvar.insert(db=mmdb, tr=tr_Method, relvar='Method Signature', tuples=[
            Method_Signature_i(SIGnum=self.signum, Method=self.name, Class=self.class_name,
                               Domain=self.domain)
        ])

        # Parse the scrall and save for later population
        self.activity_parse = ScrallParser.parse_text(scrall_text=self.method_parse.activity, debug=False)

        # Populate the method
        self.anum = Activity.populate(tr=tr_Method, action_text=self.activity_parse, subsys=subsys, domain=self.domain)

        # Populate the executing instance (self) flow
        self.xi_flow = Flow.populate_instance_flow(cname=self.class_name, anum=self.anum, domain=self.domain,
                                                   label='me', single=True, activity_tr=tr_Method)
        _logger.info(f"INSERT Instance Flow (method me): [{self.domain}:{self.class_name}:{self.name}:"
                     f"{self.xi_flow.fid}]")
        Relvar.insert(db=mmdb, tr=tr_Method, relvar='Method', tuples=[
            Method_i(Anum=self.anum, Name=self.name, Class=self.class_name, Domain=self.domain,
                     Executing_instance_flow=self.xi_flow.fid)
        ])
        pass
        Relvar.insert(db=mmdb, relvar='Synchronous Output', tuples=[
            Synchronous_Output_i(Anum=self.anum, Domain=self.domain, Type=m_parse.flow_out)
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
                Parameter_i(Name=p['name'], Signature=self.signum, Domain=self.domain, Type=p['type'])
            ])
            Transaction.execute(db=mmdb, name=tr_Parameter)  # Method parameter
            _logger.info("Transaction closed: Populating parameter")

        # Output flow (created by output flow action when it is populated)

    def process_execution_units(self, method_output_types: dict[str, Method_Output_Type]):
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

        method_data = MethodActivityAP(
            anum=self.anum, domain=self.domain, cname=self.class_name, opname=self.name, signum=self.signum,
            xiflow=self.xi_flow, activity_path=self.path, domain_method_output_types=method_output_types,
            parse=self.activity_parse[0], scrall_text=self.method_parse.activity)

        # Populate the Method Actions
        self.activity_obj = Activity(activity_data=method_data)
        self.activity_obj.pop_actions()

    def post_process(self):
        """
        """
        self.activity_obj.prep_for_execution()


