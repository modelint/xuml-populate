"""
method.py – Process parsed method to populate the metamodel db
"""

import logging
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from pyral.relation import Relation  # For debugging
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.signature import Signature
from xuml_populate.populate.activity import Activity
from xuml_populate.populate.mm_type import MMtype
from xuml_populate.populate.mmclass_nt import Method_Signature_i, Method_i, Parameter_i, Synchronous_Output_i

_logger = logging.getLogger(__name__)

# Transactions
tr_Method = "Method"


class Method:
    """
    Populate all relevant Method relvars
    """
    subsys_method_path = None
    me_flow = None  # Executing instance flow

    @classmethod
    def populate(cls, mmdb: str, domain_name: str, subsys_name: str, m_parse):
        """
        Populate a method
        """
        class_name = m_parse.class_name

        Transaction.open(mmdb, tr_Method)
        _logger.info("Transaction open: Populating method")

        # Create the signature
        signum = Signature.populate(mmdb, tr=tr_Method, subsys=subsys_name, domain=domain_name)
        Relvar.insert(mmdb, tr=tr_Method, relvar='Method_Signature', tuples=[
            Method_Signature_i(SIGnum=signum, Method=m_parse.method, Class=class_name, Domain=domain_name)
        ])

        # Populate the method
        anum = Activity.populate_method(mmdb=mmdb, tr=tr_Method, action_text=m_parse.activity,
                                        cname=class_name,
                                        method=m_parse.method,
                                        subsys=subsys_name, domain=domain_name)

        # Populate the executing instance (me) flow
        cls.me_flow = Flow.populate_instance_flow(mmdb, cname=class_name, activity=anum, domain=domain_name,
                                                  label='me', single=True)
        _logger.info(f"INSERT Instance Flow (method me): [{domain_name}:{class_name}:{m_parse.method}:"
                     f"{cls.me_flow.fid}]")
        Relvar.insert(mmdb, tr=tr_Method, relvar='Method', tuples=[
            Method_i(Anum=anum, Name=m_parse.method, Class=class_name, Domain=domain_name,
                     Executing_instance_flow=cls.me_flow.fid)
        ])

        Transaction.execute(mmdb, tr_Method)  # Populate empty method
        _logger.info("Transaction closed: Populating method")

        # Add input flows (parameters)
        for p in m_parse.flows_in:
            _logger.info("Transaction open: Populating method parameter")
            Transaction.open(tclral=mmdb)  # Method parameter
            # Populate the Parameter's type if it hasn't already been populated
            MMtype.populate_unknown(mmdb, name=p['type'], domain=domain_name)

            input_fid = Flow.populate_data_flow_by_type(mmdb, mm_type=p['type'], activity=anum,
                                                        domain=domain_name, label=p['name']).fid

            _logger.info(f"INSERT Scalar Flow (method input): ["
                         f"{domain_name}:{class_name}:{m_parse.method}:^{p['name']}:{input_fid}]")
            Relvar.insert(relvar='Parameter', tuples=[
                Parameter_i(Name=p['name'], Signature=signum, Domain=domain_name,
                            Input_flow=input_fid, Activity=anum, Type=p['type'])
            ])
            Transaction.execute()  # Method parameter
            _logger.info("Transaction closed: Populating parameter")

        # Add output flow
        if m_parse.flow_out:
            # Populate Synchronous Output and an associated output Data Flow
            Transaction.open(mmdb)
            output_fid = Flow.populate_data_flow_by_type(mmdb, label=None, mm_type=m_parse.flow_out,
                                                         activity=anum, domain=domain_name).fid
            Relvar.insert(relvar='Synchronous_Output', tuples=[
                Synchronous_Output_i(Anum=anum, Domain=domain_name,
                                     Output_flow=output_fid, Type=m_parse.flow_out)
            ])
            _logger.info(f"INSERT Flow (method output): ["
                         f"{domain_name}:{class_name}:{m_parse.method}:^{output_fid}]")
            Transaction.execute()
