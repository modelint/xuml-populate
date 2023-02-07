"""
signature.py – Populate a Signature in PyRAL
"""

import logging
from PyRAL.relvar import Relvar
from typing import TYPE_CHECKING
from class_model_dsl.populate.element import Element
from class_model_dsl.populate.pop_types import Signature_i

if TYPE_CHECKING:
    from tkinter import Tk


class Signature:
    """
    Create a Signature relation with a unique id
    """
    _logger = logging.getLogger(__name__)

    @classmethod
    def populate(cls, mmdb: 'Tk', subsys_name: str, domain_name: str) -> str:
        """Constructor"""

        # Populate
        SIGnum = Element.populate_unlabeled_subsys_element(mmdb, prefix='SIG',
                                                           subsystem_name=subsys_name,
                                                           domain_name=domain_name)
        Relvar.insert(relvar='Signature', tuples=[
            Signature_i(SIGnum=SIGnum, Domain=domain_name)
        ])
        return SIGnum

        # Just enough here to support Activity Subsystem population
        # TODO: Add the rest of this subsystem later