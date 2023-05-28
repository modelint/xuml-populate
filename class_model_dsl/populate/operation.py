"""
operation.py – Convert parsed operation to a relation
"""

import logging
from PyRAL.transaction import Transaction
from PyRAL.relvar import Relvar
from class_model_dsl.populate.signature import Signature
from class_model_dsl.populate.activity import Activity
from class_model_dsl.populate.flow import Flow
from class_model_dsl.populate.pop_types import Op_Signature_i, Op_i, Parameter_i, Flow_i
from class_model_dsl.parse.method_parser import MethodParser
from pathlib import Path

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tkinter import Tk

class Operation:
    """
    Create a operation relation
    """
    _logger = logging.getLogger(__name__)
    subsys_method_path = None

    @classmethod
    def parse(cls, op_file:Path, debug=False):
        """
        Parse the method file yielding a parsed method signature and then parse the scrall separately.

        :param op_file:
        :param debug:
        :return:
        """
        return OperationParser.parse(op_path=op_file, debug=False)

    @classmethod
    def populate(cls, mmdb: 'Tk', domain_name: str, subsys_name: str, class_name: str):
        """
        Populate all operations for a given EE
        """

        op_path = cls.subsys_method_path / class_name
        for op_file in op_path.glob("*.op"):
            parsed_op = cls.parse(op_file)

            Transaction.open(tclral=mmdb)

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

            Transaction.execute()
            pass


            # Add parameters
            for p in parsed_method.flows_in:
                Transaction.open(tclral=mmdb)
                flowid = Flow.populate(mmdb, anum=anum, domain_name=domain_name, flow_type=p['type'])
                Relvar.insert(relvar='Parameter', tuples=[
                    Parameter_i(Name=p['name'], Signature=signum, Domain=domain_name,
                                Input_flow=flowid, Activity=anum)
                ])
                Transaction.execute()
            pass

