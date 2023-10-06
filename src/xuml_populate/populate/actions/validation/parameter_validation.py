"""
parameter_validation.py – Verify that a parameter is defined
"""

import logging
from xuml_populate.config import mmdb
from xuml_populate.exceptions.action_exceptions import UndefinedParameter, UndefinedMethod
from xuml_populate.populate.actions.aparse_types import Activity_ap
from pyral.relation import Relation

_logger = logging.getLogger(__name__)

def validate_param(name: str, activity: Activity_ap):
    """
    Raise an exception if the specified Parameter is not defined

    :param name:  Parameter name
    :param activity:  Activity context
    """
    # TODO: Only works for Method Signature now. Add State and Operation Signatures later
    domain = activity.domain
    anum = activity.anum

    # Method signature
    if activity.cname and activity.opname:
        R = f"Method:<{activity.opname}>, Class:<{activity.cname}>, Domain:<{domain}>"
        result = Relation.restrict(mmdb, relation='Method_Signature', restriction=R)
        if not result.body:
            raise UndefinedMethod
        signum = result.body[0]['SIGnum']

        R = f"Name:<{name}>, Signature:<{signum}>, Activity:<{anum}>, Domain:<{domain}>"
        result = Relation.restrict(mmdb, relation='Parameter', restriction=R)
        if not result.body:
            raise UndefinedParameter
        return

    # State signature
    if activity.sname:
        # Fail until validation is added
        raise UndefinedParameter

    # Operation signature
    if activity.eename:
        # Fail until validation is added
        raise UndefinedParameter

