"""
class_model.py – Parses an xUML class model file
"""

import sys
import logging
from pathlib import Path
from class_model_dsl.parse.model_parser import ModelParser
from class_model_dsl.mp_exceptions import ModelParseError, MPIOException
from class_model_dsl.database.sm_meta_db import SMmetaDB
from class_model_dsl.populate.domain import Domain

class ClassModel:

    def __init__(self, path: Path):
        """Constructor"""
        self.logger = logging.getLogger(__name__)
        self.xuml_model_path = path

        self.db = SMmetaDB(rebuild=True)
        self.population = {relvar_name: [] for relvar_name in self.db.MetaData.tables.keys()}
        self.table_names = [t for t in self.db.MetaData.tables.keys()]
        self.table_headers = { tname: [attr.name for attr in self.db.MetaData.tables[tname].c] for tname in self.table_names }
        self.scope = {}
        self.model = None

        self.logger.info("Parsing the model")
        # Parse the model
        try:
            self.model = ModelParser(model_file_path=self.xuml_model_path, debug=True)
        except MPIOException as e:
            sys.exit(e)
        try:
            self.subsystem = self.model.parse()
        except ModelParseError as e:
            sys.exit(e)

        self.Populate()

    def Insert(self, table_name, instance):
        """Insert the instance in the named table dictionary"""
        instance_dict = dict(
            zip(self.table_headers[table_name], instance)
        )
        self.population[table_name].append(instance_dict)

    def Populate(self):
        """Populate the database from the parsed input"""

        self.logger.info("Populating the model")
        Domain(model=self, parse_data=self.subsystem)

        self.logger.info("Inserting relations into schema")
        # Test populating domain relvar
        # t = self.db.MetaData.tables['Domain']
        # t = SMmetaDB.Relvars['Domain']
        # p = self.population['Domain']
        # self.db.Connection.execute(t.insert(), p)
        # print()
        for relvar_name, relation in self.population.items():
            t = SMmetaDB.Relvars[relvar_name]
            if relation:
                self.db.Connection.execute(t.insert(), relation)  # Sqlalchemy populates the table schema
