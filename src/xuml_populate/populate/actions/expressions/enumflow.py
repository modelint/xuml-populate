""" enumflow.py -- Populate a scalar flow for an enum scalar expression """

# System
import logging
from typing import TYPE_CHECKING


# Model Integration
from scrall.parse.visitor import Enum_a
from pyral.relation import Relation

# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.flow import Flow
from xuml_populate.config import mmdb

_logger = logging.getLogger(__name__)

class EnumFlow:
    """

    """

    def __init__(self, parse: Enum_a, activity: 'Activity'):
        self.enum_value = parse.value.name
        self.activity = activity

    def populate_attr_assignment(self, class_name: str, attr_name: str):
        """
        Use a class attribute to find the enum type

        Args:
            class_name:
            attr_name:

        Returns:

        """
        R = f"Name:<{attr_name}>, Class:<{class_name}>, Domain:<{self.activity.domain}>"
        attr_r = Relation.restrict(db=mmdb, relation="Attribute", restriction=R)
        if len(attr_r.body) != 1:
            msg = (f"Attribute {self.activity.domain}::{class_name}.{attr_name} not defined "
                   f"in {self.activity.activity_path}")
            _logger.error(msg)
            raise ActionException(msg)
        scalar_type = attr_r.body[0]["Scalar"]
        # Find the type name
        # Determine the flow type
        f = Flow.populate_scalar_flow(scalar_type=scalar_type, anum=self.activity.anum, domain=self.activity.domain,
                                      value=self.enum_value, label=self.enum_value)
        return f
