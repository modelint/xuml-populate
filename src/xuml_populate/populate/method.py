"""
method.py – Process parsed method to populate the metamodel db
"""
# System
import logging

# Model Integration
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from pyral.relation import Relation  # For debugging

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.signature import Signature
from xuml_populate.populate.activity import Activity
from xuml_populate.populate.mm_type import MMtype
from xuml_populate.populate.mmclass_nt import (Method_Signature_i, Method_i, Parameter_i, Synchronous_Output_i)

_logger = logging.getLogger(__name__)

# Transactions
tr_Method = "Method"
tr_Parameter = "Parameter"
tr_OutputFlow = "OutputFlow"


class Method:
    """
    Populate all relevant Method relvars
    """
    def __init__(self, domain: str, subsys: str, m_parse, parse_actions: bool):
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
        self.parse = m_parse
        self.xi_flow = None
        self.class_name = m_parse.class_name
        self.signnum = None
        self.anum = None

        Transaction.open(db=mmdb, name=tr_Method)
        _logger.info("Transaction open: Populating method")

        # Create the Method Signature
        self.signum = Signature.populate(tr=tr_Method, subsys=self.subsys, domain=self.domain)
        Relvar.insert(db=mmdb, tr=tr_Method, relvar='Method Signature', tuples=[
            Method_Signature_i(SIGnum=self.signum, Method=self.parse.method, Class=self.class_name, Domain=domain)
        ])

        # Populate the method
        self.anum = Activity.populate_method(
            tr=tr_Method, action_text=self.parse.activity,
            cname=self.class_name, method=self.parse.method, subsys=self.subsys, domain=self.domain,
            parse_actions=parse_actions)

        # Populate the executing instance (self) flow
        self.xi_flow = Flow.populate_instance_flow(cname=self.class_name, anum=self.anum, domain=self.domain,
                                                   label='me', single=True, activity_tr=tr_Method)
        _logger.info(f"INSERT Instance Flow (method me): [{self.domain}:{self.class_name}:{self.parse.method}:"
                     f"{self.xi_flow.fid}]")
        Relvar.insert(db=mmdb, tr=tr_Method, relvar='Method', tuples=[
            Method_i(Anum=self.anum, Name=self.parse.method, Class=self.class_name, Domain=self.domain,
                     Executing_instance_flow=self.xi_flow.fid)
        ])

        Transaction.execute(db=mmdb, name=tr_Method)  # Populate empty method
        _logger.info("Transaction closed: Populating method")

        # Add input flows (parameters)
        for p in self.parse.flows_in:
            # Populate the Parameter's type if it hasn't already been populated
            MMtype.populate_unknown(name=p['type'], domain=self.domain)

            _logger.info("Transaction open: Populating method parameter")
            Transaction.open(db=mmdb, name=tr_Parameter)

            input_fid = Flow.populate_data_flow_by_type(
                mm_type=p['type'], anum=self.anum, domain=self.domain,
                label=p['name'], activity_tr=tr_Parameter).fid

            _logger.info(f"INSERT Scalar Flow (method input): ["
                         f"{self.domain}:{self.class_name}:{self.parse.method}:^{p['name']}:{input_fid}]")
            Relvar.insert(db=mmdb, tr=tr_Parameter, relvar='Parameter', tuples=[
                Parameter_i(Name=p['name'], Signature=self.signum, Domain=self.domain,
                            Input_flow=input_fid, Activity=self.anum, Type=p['type'])
            ])
            Transaction.execute(db=mmdb, name=tr_Parameter)  # Method parameter
            _logger.info("Transaction closed: Populating parameter")

        # Output flow (created by output flow action when it is populated)
