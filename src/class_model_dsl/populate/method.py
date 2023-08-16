"""
method.py – Convert parsed method to a relation
"""

import logging
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from class_model_dsl.populate.flow import Flow
from class_model_dsl.populate.signature import Signature
from class_model_dsl.populate.activity import Activity
from class_model_dsl.populate.mm_type import MMtype
from class_model_dsl.populate.pop_types import Method_Signature_i, Method_i, Parameter_i, Synchronous_Output_i
from class_model_dsl.parse.method_parser import MethodParser
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
    def parse(cls, method_file:Path, debug=False):
        """
        Parse the method file yielding a parsed method signature and then parse the scrall separately.

        :param method_file:
        :param debug:
        :return:
        """
        return MethodParser.parse(method_path=method_file, debug=False)

    @classmethod
    def populate(cls, mmdb: 'Tk', domain_name: str, subsys_name: str, class_name: str):
        """
        Populate all methods for a given class
        """

        class_method_path = cls.subsys_method_path / class_name
        for method_file in class_method_path.glob("*.mtd"):
            parsed_method = cls.parse(method_file)

            Transaction.open(tclral=mmdb)  # Populate empty method
            cls._logger.info("Transaction open: Populating method")

            # Create the signature
            signum = Signature.populate(mmdb, subsys_name=subsys_name, domain_name=domain_name)
            Relvar.insert(relvar='Method_Signature', tuples=[
                Method_Signature_i(SIGnum=signum, Method=parsed_method.method, Class=class_name, Domain=domain_name)
            ])

            # Create the method
            # Open method file and
            anum = Activity.populate_method(mmdb=mmdb, action_text=parsed_method.activity,
                                            class_name=class_name,
                                            method_name=parsed_method.method,
                                            subsys_name=subsys_name, domain_name=domain_name)

            # Populate the executing instance (xi) flow
            cls.xi_fid = Flow.populate_instance_flow(mmdb, cname=class_name, activity=anum, domain=domain_name,
                                                     label=None, single=True)
            cls._logger.info(f"INSERT Instance Flow (method xi): [{domain_name}:{class_name}:{parsed_method.method}:"
                             f"{cls.xi_fid}]")
            Relvar.insert(relvar='Method', tuples=[
                Method_i(Anum=anum, Name=parsed_method.method, Class=class_name, Domain=domain_name,
                         Executing_instance_flow=cls.xi_fid)
            ])

            Transaction.execute() # Populate empty method
            cls._logger.info("Transaction closed: Populating method")



            # Add input flows (parameters)
            for p in parsed_method.flows_in:
                cls._logger.info("Transaction open: Populating method parameter")
                Transaction.open(tclral=mmdb) # Method parameter
                # Populate the Parameter's type if it hasn't already been populated
                MMtype.populate_unknown(mmdb, name=p['type'], domain=domain_name)

                input_flow = Flow.populate_data_flow_by_type(mmdb, mm_type=p['type'], activity=anum,
                                                             domain=domain_name, label=p['name'])
                cls._logger.info(f"INSERT Scalar Flow (method input): ["
                                 f"{domain_name}:{class_name}:{parsed_method.method}:^{p['name']}:{input_flow}]")
                Relvar.insert(relvar='Parameter', tuples=[
                    Parameter_i(Name=p['name'], Signature=signum, Domain=domain_name,
                                Input_flow=input_flow, Activity=anum, Type=p['type'])
                ])
                Transaction.execute() # Method parameter
                cls._logger.info("Transaction closed: Populating parameter")

            # Add output flow
            if parsed_method.flow_out:
                # Populate Synchronous Output and an associated output Data Flow
                Transaction.open(mmdb)
                of_id = Flow.populate_data_flow_by_type(mmdb, label=None, mm_type=parsed_method.flow_out,
                                                activity=anum, domain=domain_name)
                Relvar.insert(relvar='Synchronous_Output', tuples=[
                    Synchronous_Output_i(Anum=anum, Domain=domain_name,
                                         Output_flow=of_id, Type=parsed_method.flow_out)
                ])
                cls._logger.info(f"INSERT Flow (method output): ["
                                 f"{domain_name}:{class_name}:{parsed_method.method}:^{of_id}]")
                Transaction.execute()
