"""
operation.py – Convert parsed operation to a relation
"""

import logging
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from class_model_dsl.populate.flow import Flow
from class_model_dsl.populate.signature import Signature
from class_model_dsl.populate.activity import Activity
from class_model_dsl.populate.mm_type import MMtype
from class_model_dsl.populate.pop_types import Op_Signature_i, Op_i, Parameter_i,\
    Asynchronous_Operation_i, Synchronous_Operation_i, Synchronous_Output_i
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

    @classmethod
    def populate(cls, mmdb: 'Tk', subsys_name: str, domain_name: str, opfile: Path, first_op: bool):
        """
        Populate one operation for an EE

        :param mmdb:
        :param subsys_name:
        :param domain_name:
        :param opfile:
        :param first_op:
        :return:
        """
        if not first_op:
            ## On the first op we already have an open transaction for the EE population
            ## For each subsequent op, a new transaction must be opened
            logging.info("Transaction open: Operation")
            Transaction.open(tclral=mmdb)

        parsed_op = OpParser.parse(op_path=opfile, debug=False)

        # Create the signature
        signum = Signature.populate(mmdb, subsys_name=subsys_name, domain_name=domain_name)
        Relvar.insert(relvar='Operation_Signature', tuples=[
            Op_Signature_i(SIGnum=signum, Operation=parsed_op.op, EE=parsed_op.ee, Domain=domain_name)
        ])

        Relvar.insert(relvar='Operation', tuples=[
            Op_i(Name=parsed_op.op, EE=parsed_op.ee, Domain=domain_name, Direction=parsed_op.op_type)
        ])
        anum = Activity.populate_operation(mmdb=mmdb, action_text=parsed_op.activity,
                                           ee_name=parsed_op.ee, subsys_name=subsys_name, domain_name=domain_name,
                                           synchronous=True if parsed_op.flow_out else False)

        if parsed_op.flow_out:
            Relvar.insert(relvar='Synchronous_Operation', tuples=[
                Synchronous_Operation_i(Name=parsed_op.op, EE=parsed_op.ee, Domain=domain_name, Anum=anum)
            ])
        else:
            Relvar.insert(relvar='Asynchronous_Operation', tuples=[
                Asynchronous_Operation_i(Name=parsed_op.op, EE=parsed_op.ee, Domain=domain_name, Anum=anum)
            ])

        Transaction.execute()
        logging.info("Transaction closed: Operation")

        # Add parameters
        for p in parsed_op.flows_in:
            cls._logger.info("Transaction open: Populating operation parameter")
            Transaction.open(tclral=mmdb) # Operation parameter
            # Populate the Parameter's type if it hasn't already been populated
            MMtype.populate_unknown(mmdb, name=p['type'], domain=domain_name)
            input_flow = Flow.populate_data_flow_by_type(mmdb, mm_type=p['type'], activity=anum,
                                                         domain=domain_name, label=None)
            Relvar.insert(relvar='Parameter', tuples=[
                Parameter_i(Name=p['name'], Signature=signum, Domain=domain_name,
                            Input_flow=input_flow, Activity=anum, Type=p['type'])
            ])
            Transaction.execute() # Operation parameter
            logging.info("Transaction closed: Parameter")

        # Add output flow
        if parsed_op.flow_out:
            # Populate Synchronous Output and an associated output Data Flow
            Transaction.open(mmdb)
            of_id = Flow.populate_data_flow_by_type(mmdb, label=None, mm_type=parsed_op.flow_out,
                                                    activity=anum, domain=domain_name)
            Relvar.insert(relvar='Synchronous_Output', tuples=[
                Synchronous_Output_i(Anum=anum, Domain=domain_name,
                                     Output_flow=of_id, Type=parsed_op.flow_out)
            ])
            Transaction.execute()
