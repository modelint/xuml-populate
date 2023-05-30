"""
operation.py – Convert parsed operation to a relation
"""

import logging
from PyRAL.transaction import Transaction
from PyRAL.relvar import Relvar
from class_model_dsl.populate.signature import Signature
from class_model_dsl.populate.activity import Activity
from class_model_dsl.populate.flow import Flow
from class_model_dsl.populate.pop_types import Op_Signature_i, Op_i, Parameter_i,\
    Asynchronous_Ingress_Operation_i, Synchronous_Ingress_Operation_i, Ingress_Operation_i, Egress_Operation_i
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
        :param ee_name:
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
            Op_i(Name=parsed_op.op, EE=parsed_op.ee, Domain=domain_name)
        ])
        if parsed_op.op_type == 'egress':
            # There is no activity associated with an Egresss Operation
            Relvar.insert(relvar='Egress_Operation', tuples=[
                Egress_Operation_i(Name=parsed_op.op, EE=parsed_op.ee, Domain=domain_name)
            ])
        else:
            # Create the Ingress Operation and its Activity
            anum = Activity.populate_operation(mmdb=mmdb, action_text=parsed_op.activity,
                                               ee_name=parsed_op.ee, subsys_name=subsys_name, domain_name=domain_name,
                                               synchronous=True if parsed_op.flows_out else False)

            Relvar.insert(relvar='Ingress_Operation', tuples=[
                Ingress_Operation_i(Name=parsed_op.op, EE=parsed_op.ee, Domain=domain_name)
            ])
            if parsed_op.flows_out:
                Relvar.insert(relvar='Synchronous_Ingress_Operation', tuples=[
                    Synchronous_Ingress_Operation_i(Name=parsed_op.op, EE=parsed_op.ee, Domain=domain_name, Anum=anum)
                ])
            else:
                Relvar.insert(relvar='Asynchronous_Ingress_Operation', tuples=[
                    Asynchronous_Ingress_Operation_i(Name=parsed_op.op, EE=parsed_op.ee, Domain=domain_name, Anum=anum)
                ])

        Transaction.execute()
        logging.info("Transaction closed: Operation")

        # Add parameters
        for p in parsed_op.flows_in:
            Transaction.open(tclral=mmdb)
            logging.info("Transaction open: Parameter")
            flowid = Flow.populate(mmdb, anum=anum, domain_name=domain_name, flow_type=p['type'])
            Relvar.insert(relvar='Parameter', tuples=[
                Parameter_i(Name=p['name'], Signature=signum, Domain=domain_name,
                            Input_flow=flowid, Activity=anum)
            ])
            Transaction.execute()
            logging.info("Transaction closed: Parameter")
