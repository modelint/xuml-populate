"""
method.py – Convert parsed method to a relation
"""

import logging
from PyRAL.transaction import Transaction
from PyRAL.relvar import Relvar
from class_model_dsl.populate.signature import Signature
from class_model_dsl.populate.pop_types import Method_Signature_i, Method_i,\
    Synchronous_Output_i, Synchronous_Activity_i, Activity_i

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tkinter import Tk

class Method:
    """
    Create a method relation
    """
    _logger = logging.getLogger(__name__)

    @classmethod
    def populate(cls, mmdb: 'Tk', domain_name: str, subsys_name: str, class_name: str, record):
        """Constructor"""

        cls.record = record

        Transaction.open(tclral=mmdb)

        # Create the signature
        signum = Signature.populate(mmdb, subsys_name=subsys_name, domain_name=domain_name)
        Relvar.insert(relvar='Method Signature', tuples=[
            Method_Signature_i(SIGnum=signum, Method=record['op_name'], Class=class_name, Domain=domain_name)
        ])
        Relvar.insert(relvar='Method', tuples=[
            Method_i(Anum=None, Name=record['op_name'], Class=class_name, Domain=domain_name)
        ])

        # Create the method and method signature


        Transaction.execute()

