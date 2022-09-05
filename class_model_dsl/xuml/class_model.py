"""
class_model.py – Parses an xUML class model file
"""

import sys
import logging
from pathlib import Path
from class_model_dsl.parse.model_parser import ModelParser
from class_model_dsl.mp_exceptions import ModelParseError, MPIOException
from class_model_dsl.database.sm_meta_db import SMmetaDB
from class_model_dsl.populate.mm_class import MMclass

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

    def Populate(self):
        """Populate the database from the parsed input"""

        # Insert the domain relation
        self.population['Domain'] = [{'Name': self.subsystem.domain}, ]

        # Insert classes
        for c in self.subsystem.classes:
            MMclass(model=self, domain=self.subsystem.domain, parse_data=c)

        print("Look at model")