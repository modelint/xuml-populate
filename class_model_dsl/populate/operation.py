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
from class_model_dsl.parse.op_parser import OpParser
from pathlib import Path

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tkinter import Tk

class Operation:
    """
    Create a operation relation
    """
    _logger = logging.getLogger(__name__)
    subsys_op_path = None

    @classmethod
    def parse(cls, op_file:Path, debug=False):
        """
        Parse the op file yielding a parsed op signature and then parse the scrall separately.

        :param op_file:
        :param debug:
        :return:
        """
        return OpParser.parse(op_path=op_file, debug=False)

    @classmethod
    def populate(cls, mmdb: 'Tk', domain_name: str, subsys_name: str, class_name: str):
        """
        Populate all operations for a given EE
        """

        op_path = cls.subsys_op_path / class_name
        for op_file in op_path.glob("*.op"):
            parsed_op = cls.parse(op_file)

            Transaction.open(tclral=mmdb)

            # Create the signature
            signum = Signature.populate(mmdb, subsys_name=subsys_name, domain_name=domain_name)
            Relvar.insert(relvar='Op_Signature', tuples=[
                Op_Signature_i(SIGnum=signum, Op=parsed_op.op, EE=class_name, Domain=domain_name)
            ])

            # Create the operation
            anum = Activity.populate_operation(mmdb=mmdb, action_text=parsed_op.activity,
                                            ee=class_name,
                                            op_name=parsed_method.method,
                                            subsys_name=subsys_name, domain_name=domain_name)

            Relvar.insert(relvar='Operation', tuples=[
                Op_i(Anum=anum, Name=parsed_op.method, EE=class_name, Domain=domain_name)
            ])

            Transaction.execute()
            pass


            # Add parameters
            for p in parsed_op.flows_in:
                Transaction.open(tclral=mmdb)
                flowid = Flow.populate(mmdb, anum=anum, domain_name=domain_name, flow_type=p['type'])
                Relvar.insert(relvar='Parameter', tuples=[
                    Parameter_i(Name=p['name'], Signature=signum, Domain=domain_name,
                                Input_flow=flowid, Activity=anum)
                ])
                Transaction.execute()
            pass

