"""
class_accessor.py – Populate a Class Accessor action instance in PyRAL
"""

# System
import logging
from typing import Optional

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.mmclass_nt import Class_Accessor_i
from xuml_populate.populate.flow import Flow

_logger = logging.getLogger(__name__)

tr_Class_Accessor = "Class Accessor"

class ClassAccessor:
    """
    Create all relations for a Class Accessor
    """

    @classmethod
    def populate(cls, name: str, anum: str, domain: str) -> Optional[str]:
        """
        Populate the Class Accessor Action or return nothing if the name is not a class

        :param name:  A name which may or may not correspond to a class
        :param anum:  The enclosing anum
        :param domain:  The current domain
        :return: The output flow id of an existing or newly populated class accessor or none name is not a class
        """
        # Return None if the name does not match any defined Class
        R = f"Name:<{name}>, Domain:<{domain}>"
        class_r = Relation.restrict(db=mmdb, relation='Class', restriction=R)
        if not class_r.body:
            return None

        # Return flow id of existing Class Accessor
        R = f"Class:<{name}>, Activity:<{anum}>, Domain:<{domain}>"
        ca_r = Relation.restrict(db=mmdb, relation='Class Accessor', restriction=R)
        if ca_r.body:
            return ca_r.body[0]["Output_flow"]

        # Populate a Class Accessor and Multiple Instance Flow returning the flow id
        Transaction.open(db=mmdb, name=tr_Class_Accessor)
        output_flow = Flow.populate_instance_flow(cname=name, anum=anum, domain=domain, label=None)
        Relvar.insert(db=mmdb, relvar='Class_Accessor', tuples=[
            Class_Accessor_i(Class=name, Activity=anum, Domain=domain, Output_flow=output_flow.fid)
        ])
        Transaction.execute(db=mmdb, name=tr_Class_Accessor)
        return output_flow.fid
