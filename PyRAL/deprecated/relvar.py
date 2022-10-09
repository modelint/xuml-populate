"""
relvar.py -- Proxy for a TclRAL relvar
"""
import logging
from database import db
from typing import List
from rtypes import Attribute
from transaction import Transaction


class Relvar:
    """
    Proxy for a TclRAL relvar

    """

    def __init__(self, name: str, header: List[Attribute], identifiers: List[List[str]]):
        """

        :param name:
        :param header:
        """
        self.logger = logging.getLogger(__name__)
        self.name = name
        self.header = header
        self.identifiers = identifiers

        self.create()

    def create(self):
        """
        Create in TclRAL
        :return:
        """

        # flatten header into a list of name, type fields
        attr_fields = [attr_field for attr in [list(a) for a in self.header] for attr_field in attr]
        # Convert this list into a string of the format: {name type ...}
        # Note surrounding braces are doubled to escape the brace character
        header_string = f"{{{' '.join(list(attr_fields))}}}"

        # Flatten list of identifiers into a string with each id surrounded by {}
        id_string = ' '.join(['{' + ' '.join(i) + '}' for i in self.identifiers])

        statement = f"relvar create {self.name} {header_string} {id_string}"
        Transaction.update_schema(statement)
        Transaction.build_schema()
        # db.eval(statement)
        self.logger.info(f"Added create relvar {self.name} to transaction.")
        # result = db.eval("relvar names")
        # self.logger.info(f'Relvars in db: [{result}]')

        pass
