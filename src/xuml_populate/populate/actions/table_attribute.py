""" table_attribute.py - Provides table attribute functions """

import logging
from xuml_populate.config import mmdb
from xuml_populate.exceptions.action_exceptions import UndefinedTableAttribute
from pyral.relvar import Relvar
from pyral.relation import Relation

_logger = logging.getLogger(__name__)


class TableAttribute:
    """
    Populates the Table and all unconditionally related classes.
    This includes Table Attribute, Model Attribute and Table Flow
    """

    @classmethod
    def scalar(cls, name: str, table: str, domain: str) -> str:
        """
        Returns the name of the Scalar (Type) of the specified Attribute.

        Raises an exception if the Table Attribute is not defined on the specified Table.

        :param name:  Attribute name
        :param table: Table name
        :param domain:  Domain name
        :return: Name of Table Attribute's Scalar (Type)
        """
        R = f"Name:<{name}>, Table:<{table}>, Domain:<{domain}>"
        result = Relation.restrict(mmdb, relation='Table_Attribute', restriction=R)
        if not result.body:
            _logger.error(f"Undefined table attribute: [{name}:{domain}]")
            raise UndefinedTableAttribute
        return result.body[0]['Scalar']
