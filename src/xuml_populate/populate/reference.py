"""
reference.py – Functionality to manage referential attributes
"""

# System
import logging

# Model Integration
from pyral.relation import Relation

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.exceptions.class_exceptions import MixedTargetID, ReferenceToNonIdentifier

_logger = logging.getLogger(__name__)

def targetid(ref, rnum: str, domain: str) -> int:
    # OR restriction criteria not yet supported in PyRAL, so we iterate on the attributes
    to_id = None
    for to_attr in ref['attrs']:
        R = f"Attribute:<{to_attr}>, Class:<{ref['class']}>, Domain:<{domain}>"
        result = Relation.restrict(db=mmdb, relation='Identifier_Attribute', restriction=R)
        if not result.body:
            _logger.exception(f"No identifier found in attribute reference on [{rnum}]")
            raise ReferenceToNonIdentifier
        attr_id = int(result.body[0]['Identifier'])
        if not to_id:
            to_id = attr_id
        elif to_id != attr_id:
            _logger.exception(f"Multiple identifiers referenced on [{rnum}]")
            raise MixedTargetID
    return to_id

