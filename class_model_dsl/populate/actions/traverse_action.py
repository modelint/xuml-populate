"""
traverse_action.py – Populate a traverse action instance in PyRAL
"""

import logging
from PyRAL.relvar import Relvar
from typing import TYPE_CHECKING
from class_model_dsl.parse.scrall_visitor import PATH_a
from PyRAL.relation import Relation

if TYPE_CHECKING:
    from tkinter import Tk

class TraverseAction:
    """
    Create all relations for a Traverse Action
    """
    _logger = logging.getLogger(__name__)

    source_flow = None
    dest_flow = None
    path = None
    id = None

    @classmethod
    def build_path(cls, mmdb: 'Tk', domain_name: str, path: PATH_a):
        """
        Populate the entire Action

        :param mmdb:
        :param path:
        :param domain_name:
        :return:
        """
        for hop in path.hops:
            if type(hop).__name__ == 'R_a':
                #r = f"Rnum:R8135, Domain:{domain_name}"
                r = f"Rnum:{hop.rnum}, Domain:{domain_name}"
                # r = Relation.build_select_expr(f"Rnum:{hop.rnum}; Domain:{domain_name}")
                f = Relation.restrict(tclral=mmdb, restriction=r, relation="Relationship")
                fpy = Relation.make_pyrel(relation=f)
                if not len(fpy.body):
                    print("No such rnum in user model")
                else:
                    print("Rnum exists in user model")

                pass



        pass
