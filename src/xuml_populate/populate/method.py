"""
method.py – Convert parsed method to a relation
"""

import logging
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.signature import Signature
from xuml_populate.populate.activity import Activity
from xuml_populate.populate.mm_type import MMtype
from xuml_populate.populate.mmclass_nt import Method_Signature_i, Method_i, Parameter_i, Synchronous_Output_i
from pathlib import Path

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tkinter import Tk

class Method:
    """
    Create a method relation
    """
    _logger = logging.getLogger(__name__)
    subsys_method_path = None
    xi_fid = None  # Executing instance flow id

    @classmethod
    def populate(cls, mmdb: 'Tk', domain_name: str, subsys_name: str, m_parse):
        """
        Populate a method
        """
        class_name = m_parse.class_name

        Transaction.open(tclral=mmdb)  # Populate method
        cls._logger.info("Transaction open: Populating method")

        # Create the signature
        signum = Signature.populate(mmdb, subsys_name=subsys_name, domain_name=domain_name)
        Relvar.insert(relvar='Method_Signature', tuples=[
            Method_Signature_i(SIGnum=signum, Method=m_parse.method, Class=class_name, Domain=domain_name)
        ])

        # Create the method
        # Open method file and
        anum = Activity.populate_method(mmdb=mmdb, action_text=m_parse.activity,
                                        class_name=class_name,
                                        method_name=m_parse.method,
                                        subsys_name=subsys_name, domain_name=domain_name)

        # Populate the executing instance (xi) flow
        cls.xi_fid = Flow.populate_instance_flow(mmdb, cname=class_name, activity=anum, domain=domain_name,
                                                     label=None, single=True)
        cls._logger.info(f"INSERT Instance Flow (method xi): [{domain_name}:{class_name}:{m_parse.method}:"
                         f"{cls.xi_fid}]")
        Relvar.insert(relvar='Method', tuples=[
            Method_i(Anum=anum, Name=m_parse.method, Class=class_name, Domain=domain_name,
                     Executing_instance_flow=cls.xi_fid)
        ])

        Transaction.execute()  # Populate empty method
        cls._logger.info("Transaction closed: Populating method")

        # Add input flows (parameters)
        for p in m_parse.flows_in:
            cls._logger.info("Transaction open: Populating method parameter")
            Transaction.open(tclral=mmdb)  # Method parameter
            # Populate the Parameter's type if it hasn't already been populated
            MMtype.populate_unknown(mmdb, name=p['type'], domain=domain_name)

            input_flow = Flow.populate_data_flow_by_type(mmdb, mm_type=p['type'], activity=anum,
                                                         domain=domain_name, label=p['name'])
            cls._logger.info(f"INSERT Scalar Flow (method input): ["
                             f"{domain_name}:{class_name}:{m_parse.method}:^{p['name']}:{input_flow}]")
            Relvar.insert(relvar='Parameter', tuples=[
                Parameter_i(Name=p['name'], Signature=signum, Domain=domain_name,
                            Input_flow=input_flow, Activity=anum, Type=p['type'])
            ])
            Transaction.execute()  # Method parameter
            cls._logger.info("Transaction closed: Populating parameter")

        # Add output flow
        if m_parse.flow_out:
            # Populate Synchronous Output and an associated output Data Flow
            Transaction.open(mmdb)
            of_id = Flow.populate_data_flow_by_type(mmdb, label=None, mm_type=m_parse.flow_out,
                                            activity=anum, domain=domain_name)
            Relvar.insert(relvar='Synchronous_Output', tuples=[
                Synchronous_Output_i(Anum=anum, Domain=domain_name,
                                     Output_flow=of_id, Type=m_parse.flow_out)
            ])
            cls._logger.info(f"INSERT Flow (method output): ["
                             f"{domain_name}:{class_name}:{m_parse.method}:^{of_id}]")
            Transaction.execute()
