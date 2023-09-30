"""
class_accessor.py – Populate a Class Accessor action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING, Optional
from xuml_populate.populate.mmclass_nt import Class_Accessor_i
from xuml_populate.populate.flow import Flow
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class ClassAccessor:
    """
    Create all relations for a Class Accessor
    """

    @classmethod
    def populate(cls, mmdb: 'Tk', name: str, anum: str, domain: str) -> Optional[str]:
        """
        Populate the Class Accessor Action or return nothing if the name is not a class

        :param mmdb:  The metamodel db
        :param name:  A name which may or may not correspond to a class
        :param anum:  The enclosing activity
        :param domain:  The current domain
        :return: The output flow id of an existing or newly populated class accessor or none name is not a class
        """
        # Return None if the name does not match any defined Class
        R = f"Name:<{name}>, Domain:<{domain}>"
        result = Relation.restrict(mmdb, relation='Class', restriction=R)
        if not result.body:
            return None

        # Return flow id of exsiting Class Accessor
        R = f"Class:<{name}>, Activity:<{anum}>, Domain:<{domain}>"
        result = Relation.restrict(mmdb, relation='Class_Accessor', restriction=R)
        if result.body:
            return result.body[0].fid

        # Populate a Class Accessor and Multiple Instance Flow returning the flow id
        Transaction.open(mmdb)
        output_flow = Flow.populate_instance_flow(mmdb, cname=name, activity=anum, domain=domain, label=None)
        Relvar.insert(relvar='Class_Accessor', tuples=[
            Class_Accessor_i(Class=name, Activity=anum, Domain=domain, Output_flow=output_flow.fid)
        ])
        Transaction.execute()
        return output_flow.fid
