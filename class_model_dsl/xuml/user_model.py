"""
user_model.py – Parses a user model (aka M1 level model)

What we call the 'user model' is what the Object Management Group refers to as an M1 level model
to distinguish it from an M2 level model (metamododel) or an M0 level model which we just call a
user model or M1 population

For our purposes we will use the Elevator Management domain as one of our user / M1 test cases
"""

import sys
import logging
from pathlib import Path
from class_model_dsl.xuml.metamodel import Metamodel
from class_model_dsl.parse.model_parser import ModelParser
from class_model_dsl.mp_exceptions import ModelParseError, MPIOException
from class_model_dsl.populate.domain import Domain
from class_model_dsl.populate.lineage import Lineage
from class_model_dsl.populate.attribute import ResolveAttrTypes
from class_model_dsl.populate.mm_class import MMclass


class UserModel:
    _logger = logging.getLogger(__name__)
    user_model_path = None
    subsystem = None
    model = None

    @classmethod
    def load(cls, user_model_path: Path):
        """

        :param user_model_path:
        """
        cls.user_model_path = user_model_path

        # Parse the model
        cls._logger.info("Parsing the user model")
        try:
            cls.model = ModelParser(model_file_path=cls.user_model_path, debug=False)
        except MPIOException as e:
            sys.exit(e)
        try:
            cls.subsystem = cls.model.parse()
            pass
        except ModelParseError as e:
            sys.exit(e)

        cls.populate()
        ResolveAttrTypes()


    @classmethod
    def populate(cls):
        """Populate the database from the parsed input"""

        cls._logger.info("Populating the model")

        # Insert classes
        cls._logger.info("Populating classes")
        domain = cls.subsystem.domain['name']
        for c in cls.subsystem.classes:
            MMclass.populate(domain=domain, parse_data=c)

        # Insert relationships
        # self.logger.info("Populating relationships")
        # for r in self.parse_data.rels:
        #     Relationship(domain=self, subsys=s, parse_data=r)

        #self.domain = Domain(model=self, parse_data=self.subsystem)

        # for relvar_name, relation in self.population.items():
        #     t = SMmetaDB.Relvars[relvar_name]
        #     if relation:
        #         self.db.Connection.execute(t.insert(), relation)  # Sqlalchemy populates the table schema

        #cls._logger.info("Populating lineage")
        #Lineage(domain=self.domain)
