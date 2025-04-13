"""
operation.py – Convert parsed operation to a relation
"""

import logging
from xuml_populate.config import mmdb
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.signature import Signature
from xuml_populate.populate.activity import Activity
from xuml_populate.populate.mm_type import MMtype
from xuml_populate.populate.mmclass_nt import Operation_Signature_i, Operation_i, Parameter_i,\
    Asynchronous_Operation_i, Synchronous_Operation_i, Synchronous_Output_i

_logger = logging.getLogger(__name__)

tr_Op = "Operation"
tr_EE = "EE"
tr_Parameter = "Parameter"
tr_Output = "Synchronous Output"

class Operation:
    """
    Create a operation relation
    """

    @classmethod
    def populate(cls, tr: str, subsys: str, domain: str, parsed_op) -> str:
        """
        Populate a single operation for an EE

        (This is meant to be invoked for each operation of the EE)

        :param tr: Either "EE" or "Operation" as the name of the transaction
        :param subsys: The subsystem name
        :param domain: The domain name
        :param parsed_op:  The parsed operation
        :return: Change the transaction from "EE" to "Operation" for subsequent invocations
        """
        # The first invocation for an EE will be tr_EE in which case we know that the EE transaction is
        # still pending and we want to use that transaction to populate its first required Operation
        # Upon completion we return "Operation" as the ongoing transaction until the next EE comes along

        if tr != tr_EE:
            # On the first op we already have an open transaction for the EE population
            # For each subsequent op, a new transaction must be opened
            logging.info("Transaction open: Operation")
            Transaction.open(mmdb, tr_Op)

        # Create the signature
        signum = Signature.populate(tr=tr, subsys=subsys, domain=domain)
        Relvar.insert(mmdb, tr=tr, relvar='Operation_Signature', tuples=[
            Operation_Signature_i(SIGnum=signum, Operation=parsed_op.op, EE=parsed_op.ee, Domain=domain)
        ])

        Relvar.insert(mmdb, tr=tr, relvar='Operation', tuples=[
            Operation_i(Name=parsed_op.op, EE=parsed_op.ee, Domain=domain, Direction=parsed_op.op_type)
        ])
        anum = Activity.populate_operation(tr=tr, action_text=parsed_op.activity,
                                           ee=parsed_op.ee, subsys=subsys, domain=domain,
                                           synchronous=True if parsed_op.flow_out else False)

        if parsed_op.flow_out:
            Relvar.insert(mmdb, tr=tr, relvar='Synchronous_Operation', tuples=[
                Synchronous_Operation_i(Name=parsed_op.op, EE=parsed_op.ee, Domain=domain, Anum=anum)
            ])
        else:
            Relvar.insert(mmdb, tr=tr, relvar='Asynchronous_Operation', tuples=[
                Asynchronous_Operation_i(Name=parsed_op.op, EE=parsed_op.ee, Domain=domain, Anum=anum)
            ])

        Transaction.execute(mmdb, tr)
        logging.info("Transaction closed: Operation")

        # Add parameters
        for p in parsed_op.flows_in:

            # Populate the Parameter's type if it hasn't already been populated
            MMtype.populate_unknown(name=p['type'], domain=domain)
            _logger.info("Transaction open: Populating operation parameter")
            Transaction.open(db=mmdb, name=tr_Parameter)
            input_fid = Flow.populate_data_flow_by_type(mm_type=p['type'], anum=anum,
                                                        domain=domain, label=None, activity_tr=tr_Parameter).fid
            Relvar.insert(db=mmdb, tr=tr_Parameter, relvar='Parameter', tuples=[
                Parameter_i(Name=p['name'], Signature=signum, Domain=domain,
                            Input_flow=input_fid, Activity=anum, Type=p['type'])
            ])
            Transaction.execute(db=mmdb, name=tr_Parameter)
            logging.info("Transaction closed: Parameter")

        # Add output flow
        if parsed_op.flow_out:
            # Populate Synchronous Output and an associated output Data Flow
            Transaction.open(db=mmdb, name=tr_Output)
            of_id = Flow.populate_data_flow_by_type(label=None, mm_type=parsed_op.flow_out,
                                                    anum=anum, domain=domain, activity_tr=tr_Output).fid
            Relvar.insert(db=mmdb, tr=tr_Output, relvar='Synchronous_Output', tuples=[
                Synchronous_Output_i(Anum=anum, Domain=domain,
                                     Output_flow=of_id, Type=parsed_op.flow_out)
            ])
            Transaction.execute(db=mmdb, name=tr_Output)

        return tr_Op
