"""
method.py – Convert parsed method to a relation
"""

import logging
from PyRAL.transaction import Transaction
from PyRAL.relvar import Relvar
from class_model_dsl.populate.signature import Signature
from class_model_dsl.populate.activity import Activity
from class_model_dsl.populate.flow import Flow
from class_model_dsl.populate.pop_types import Method_Signature_i, Method_i, Parameter_i, Flow_i
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

            Relvar.insert(relvar='Method', tuples=[
                Method_i(Anum=anum, Name=parsed_method.method, Class=class_name, Domain=domain_name)
            ])

            Transaction.execute() # Populate empty method
            cls._logger.info("Transaction closed: Populating method")


            # Add parameters
            for p in parsed_method.flows_in:
                cls._logger.info("Transaction open: Populating parameter")
                Transaction.open(tclral=mmdb)
                flowid = Flow.populate(mmdb, anum=anum, domain_name=domain_name, flow_type=p['type'])
                Relvar.insert(relvar='Parameter', tuples=[
                    Parameter_i(Name=p['name'], Signature=signum, Domain=domain_name,
                                Input_flow=flowid, Activity=anum)
                ])
                Transaction.execute()
                cls._logger.info("Transaction closed: Populating parameter")
