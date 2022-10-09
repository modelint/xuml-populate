"""
schema.py -- Database schema
"""
import logging
from database import db
from typing import List
from rtypes import Attribute


class Schema:
    """
    A TclRAL transaction

    """
    _relvars = []
    _constraints = []
    _schema_build_cmd = []
    _logger = logging.getLogger(__name__)
    _result = None
    _created_relvars = None

    @classmethod
    def add_relvar(cls, name: str, header: List[Attribute], identifiers: List[List[str]]):
        """
        Add a relvar create statement

        :return:
        """
        # flatten header into a list of name, type fields
        attr_fields = [attr_field for attr in [list(a) for a in header] for attr_field in attr]
        # Convert this list into a string of the format: {name type ...}
        # Note surrounding braces are doubled to escape the brace character
        header_string = f"{{{' '.join(list(attr_fields))}}}"

        # Flatten list of identifiers into a string with each id surrounded by {}
        id_string = ' '.join(['{' + ' '.join(i) + '}' for i in identifiers])
        create_relvar_cmd = f"relvar create {name} {header_string} {id_string}"
        cls._relvars.append(create_relvar_cmd)
        pass

    @classmethod
    def build(cls):
        """
        Executes a set of Relvars and Constraints to define a database schema
        :return:
        """
        cls._schema_build_cmd = '\n'.join(cls._relvars)
        # For now let's just create the relvars
        cls._logger.info(f"Building schema with TclRAL script:\n{cls._schema_build_cmd}")
        cls._result = db.eval(cls._schema_build_cmd)
        relvar_names = db.eval("relvar names")
        cls._created_relvars = [r for r in relvar_names.split('::') if r]
        cls._logger.info(f"Completed schema build with result: [{cls._result}]")
        cls._logger.info(f"And created relvars:\n {cls._created_relvars}")
