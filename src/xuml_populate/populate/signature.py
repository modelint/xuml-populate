""" signature.py – Populate a Signature in the metamodel db """

import logging
from pyral.relvar import Relvar
from xuml_populate.config import mmdb
from xuml_populate.populate.element import Element
from xuml_populate.populate.mmclass_nt import Signature_i

_logger = logging.getLogger(__name__)

class Signature:
    """
    Populate a Signature relvar with a unique id
    """
    @classmethod
    def populate(cls, tr: str, subsys: str, domain: str) -> str:
        """

        :param tr: The name of the open transaction
        :param subsys: The subsystem name
        :param domain: The domain name
        :return: The Signature id (SIGnum)
        """

        # Populate
        SIGnum = Element.populate_unlabeled_subsys_element(tr=tr, prefix='SIG', subsystem=subsys, domain=domain)
        Relvar.insert(mmdb, tr=tr, relvar='Signature', tuples=[
            Signature_i(SIGnum=SIGnum, Domain=domain)
        ])
        return SIGnum

        # Just enough here to support Activity Subsystem population
        # TODO: Add the rest of this subsystem later