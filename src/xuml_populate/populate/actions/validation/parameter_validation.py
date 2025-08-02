"""
parameter_validation.py – Verify that a parameter is defined
"""

# System
import logging

# Model Integration
from pyral.relation import Relation

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.exceptions.action_exceptions import UndefinedParameter
from xuml_populate.populate.actions.aparse_types import ActivityAP

_logger = logging.getLogger(__name__)

def validate_param(name: str, activity: ActivityAP):
    """
    Raise an exception if the specified Parameter is not defined

    :param name:  Parameter name
    :param activity:  Activity context
    """
    # Verify that there is a populated instance of Parameter
    R = f"Name:<{name}>, Signature:<{activity.signum}>, Domain:<{activity.domain}>"
    param_r = Relation.restrict(db=mmdb, relation='Parameter', restriction=R)
    if not param_r.body:
        raise UndefinedParameter
