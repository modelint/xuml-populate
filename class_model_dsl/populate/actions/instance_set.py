""" instance_set.py """

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from class_model_dsl.populate.mm_class import MMclass
from class_model_dsl.populate.flow import Flow
from class_model_dsl.populate.actions.select_action import SelectAction
from pyral.relation import Relation
from pyral.transaction import Transaction
from class_model_dsl.exceptions.action_exceptions import NoClassOrInstanceFlowForInstanceSetName

from collections import namedtuple
Iflow = namedtuple("Iflow", "id cname")
"""Instance flow descriptor"""
Tflow = namedtuple("Tflow", "id table_type")
"""Table flow descriptor"""


if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)
class InstanceSet:
    """
    Entry point for breaking down a parsed Instance Set
    """

    @classmethod
    def process(cls, mmdb: 'Tk', anum: str, iset_parse, domain: str, activity_path: str, scrall_text: str):
        for c in iset_parse.components:
            match type(c).__name__:
                case 'N_a':
                    # Check to see if it is a class name
                    if MMclass.exists(cname=c.name, domain=domain):
                        # An encountered class name on the RHS is the source of a multiple instance flow
                        # We create that and set it as the current RHS input flow
                        Transaction.open(mmdb)
                        cls.input_instance_flow = Iflow(id=Flow.populate_instance_flow(
                            mmdb, cname=c.name, activity=anum, domain=domain, label=None), cname=c.name)
                        Transaction.execute()
                    else:
                        # Look for a labeled instance flow
                        R = f"Name:<{c.name}>, Activity:<{anum}>, Domain:<{domain}>"
                        result = Relation.restrict3(mmdb, relation='Label', restriction=R)
                        if result.body:
                            # Labeled flow found
                            cls.input_instance_flow = result.body[0]['Flow']
                        else:
                            raise NoClassOrInstanceFlowForInstanceSetName(path=activity_path, text=scrall_text,
                                                                          x=iset_parse.X)
                case 'Selection_a':
                    # Process to populate a select action, the output type does not change
                    # since we are selecting on a known class
                    cls.input_instance_flow, cls.input_instance_ctype, cls.max_mult = SelectAction.populate(
                        mmdb, input_instance_flow=cls.input_instance_flow, anum=anum, select_agroup=c, domain=domain,
                        activity_path=activity_path, scrall_text=scrall_text)

        pass