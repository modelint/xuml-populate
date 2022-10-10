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
from metamodel import Metamodel
from class_model_dsl.parse.model_parser import ModelParser
from class_model_dsl.mp_exceptions import ModelParseError, MPIOException
# from class_model_dsl.database.sm_meta_db import SMmetaDB
from class_model_dsl.populate.domain import Domain
from class_model_dsl.populate.lineage import Lineage
from class_model_dsl.populate.attribute import ResolveAttrTypes

class UserModel:

    logger = logging.getLogger(__name__)
    user_model_path = None

    @classmethod
    def load(cls, user_model_path: Path):
        cls.user_model_path = user_model_path

        # TODO work out the thread from main into UserModel to the build
        # TODO of the metamodel. See notes in Simplenote




        logger.info("Parsing the user model")
        # Parse the model
        try:
            self.model = ModelParser(model_file_path=self.xuml_model_path, debug=False)
        except MPIOException as e:
            sys.exit(e)
        try:
            self.subsystem = self.model.parse()
        except ModelParseError as e:
            sys.exit(e)


    def __init__(self, path: Path):
        """Constructor"""

        # self.db = SMmetaDB(rebuild=True)
        # self.population = {relvar_name: [] for relvar_name in self.db.MetaData.tables.keys()}
        # self.table_names = [t for t in self.db.MetaData.tables.keys()]
        # self.table_headers = { tname: [attr.name for attr in self.db.MetaData.tables[tname].c] for tname in self.table_names }
        self.scope = {}
        self.model = None
        self.domain = None

        self.logger.info("Parsing the model")
        # Parse the model
        try:
            self.model = ModelParser(model_file_path=self.xuml_model_path, debug=False)
        except MPIOException as e:
            sys.exit(e)
        try:
            self.subsystem = self.model.parse()
        except ModelParseError as e:
            sys.exit(e)


        self.Populate()
        ResolveAttrTypes()


    def CreateDB(self):
        """
        Create a metamodel database in PyRAL complete with relvars and constraints
        from a parse of the metamodel xcm file
        :return:
        """
        # TODO: Put class-attr.xcm file in a new metamodel input directory
        # TODO: parse it and store results independently of the users model .xcm

    def Insert(self, table_name, instance):
        """Insert the instance in the named table dictionary"""
        pass
        # instance_dict = dict(
        #     zip(self.table_headers[table_name], instance)
        # )
        # self.population[table_name].append(instance_dict)

    def Populate(self):
        """Populate the database from the parsed input"""

        self.logger.info("Populating the model")
        self.domain = Domain(model=self, parse_data=self.subsystem)

        self.logger.info("Inserting relations into schema")
        # for relvar_name, relation in self.population.items():
        #     t = SMmetaDB.Relvars[relvar_name]
        #     if relation:
        #         self.db.Connection.execute(t.insert(), relation)  # Sqlalchemy populates the table schema

        self.logger.info("Populating lineage")
        Lineage(domain=self.domain)

