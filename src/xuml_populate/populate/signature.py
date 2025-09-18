""" signature.py – Populate a Signature in the metamodel db """

# System
import logging

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.element import Element
from xuml_populate.populate.mmclass_nt import Signature_i

# Model Integration
from pyral.relvar import Relvar

_logger = logging.getLogger(__name__)

class Signature:
    """
    Populate a Signature relvar with a unique id
    """
    @classmethod
    def populate(cls, tr: str, domain: str) -> str:
        """
        Args:
            tr: The name of the open transaction
            domain: The domain name

        Returns:
            The Signature id (SIGnum)
        """
        # Populate
        SIGnum = Element.populate_unlabeled_spanning_element(tr=tr, prefix='SIG', domain=domain)
        Relvar.insert(db=mmdb, tr=tr, relvar='Signature', tuples=[
            Signature_i(SIGnum=SIGnum, Domain=domain)
        ])
        return SIGnum

        # Just enough here to support Activity Subsystem population
        # TODO: Add the rest of this subsystem later