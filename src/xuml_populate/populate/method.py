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


class Method:
    """
    Populate all relevant Method relvars
    """
    def __init__(self, domain: str, subsys: str, m_parse, parse_actions: bool):
        """
        Populate a method

        :param domain: The name of the domain
        :param subsys: The name of the subsystem
        :param m_parse: The parsed content of the method
        :return:
        """
        subsys_method_path = None
        me_flow = None  # Executing instance flow

        class_name = m_parse.class_name

        Transaction.open(db=mmdb, name=tr_Method)
        _logger.info("Transaction open: Populating method")

        # Create the signature
        signum = Signature.populate(tr=tr_Method, subsys=subsys, domain=domain)
        Relvar.insert(db=mmdb, tr=tr_Method, relvar='Method_Signature', tuples=[
            Method_Signature_i(SIGnum=signum, Method=m_parse.method, Class=class_name, Domain=domain)
        ])

        # Populate the method
        anum = Activity.populate_method(tr=tr_Method, action_text=m_parse.activity,
                                        cname=class_name,
                                        method=m_parse.method,
                                        subsys=subsys, domain=domain, parse_actions=parse_actions)

        # Populate the executing instance (me) flow
        self.me_flow = Flow.populate_instance_flow(cname=class_name, anum=anum, domain=domain,
                                                  label='me', single=True)
        _logger.info(f"INSERT Instance Flow (method me): [{domain}:{class_name}:{m_parse.method}:"
                     f"{self.me_flow.fid}]")
        Relvar.insert(db=mmdb, tr=tr_Method, relvar='Method', tuples=[
            Method_i(Anum=anum, Name=m_parse.method, Class=class_name, Domain=domain,
                     Executing_instance_flow=self.me_flow.fid)
        ])

        Transaction.execute(db=mmdb, name=tr_Method)  # Populate empty method
        _logger.info("Transaction closed: Populating method")

        # Add input flows (parameters)
        for p in m_parse.flows_in:
            # Populate the Parameter's type if it hasn't already been populated
            MMtype.populate_unknown(name=p['type'], domain=domain)

            _logger.info("Transaction open: Populating method parameter")
            Transaction.open(db=mmdb, name=tr_Parameter)

            input_fid = Flow.populate_data_flow_by_type(mm_type=p['type'], anum=anum,
                                                        domain=domain, label=p['name']).fid

            _logger.info(f"INSERT Scalar Flow (method input): ["
                         f"{domain}:{class_name}:{m_parse.method}:^{p['name']}:{input_fid}]")
            Relvar.insert(db=mmdb, tr=tr_Parameter, relvar='Parameter', tuples=[
                Parameter_i(Name=p['name'], Signature=signum, Domain=domain,
                            Input_flow=input_fid, Activity=anum, Type=p['type'])
            ])
            Transaction.execute(db=mmdb, name=tr_Parameter)  # Method parameter
            _logger.info("Transaction closed: Populating parameter")

        # Add output flow
        if m_parse.flow_out:
            # Populate Synchronous Output and an associated output Data Flow
            output_fid = Flow.populate_data_flow_by_type(label=None, mm_type=m_parse.flow_out,
                                                         anum=anum, domain=domain).fid
            # No transaction needed since a single tuple is inserted for this feature
            Relvar.insert(db=mmdb, relvar='Synchronous_Output', tuples=[
                Synchronous_Output_i(Anum=anum, Domain=domain,
                                     Output_flow=output_fid, Type=m_parse.flow_out)
            ])
            _logger.info(f"INSERT Flow (method output): ["
                         f"{domain}:{class_name}:{m_parse.method}:^{output_fid}]")
