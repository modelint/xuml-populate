"""
class_model.py – Parses an xUML class model file
"""

import sys
import logging
from pathlib import Path
from class_model_dsl.parse.model_parser import ModelParser
from class_model_dsl.mp_exceptions import ModelParseError, MPIOException
from class_model_dsl.database.sm_meta_db import SMmetaDB
from class_model_dsl.populate.metaclass_headers import header

class ClassModel:

    def __init__(self, path: Path):
        """Constructor"""
        self.logger = logging.getLogger(__name__)
        self.xuml_model_path = path

        self.db = SMmetaDB(rebuild=True)
        self.population = {relvar_name: [] for relvar_name in self.db.MetaData.tables.keys()}
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

        # Initialize a relations dictionary

        # Set the domain scope
        self.scope = {'domain': self.subsystem.domain}

        # Insert the domain relation
        self.population['Domain'] = [{'Name': self.scope['domain']}, ]

        # Insert classes
        for c in self.subsystem.classes:
            self.scope['class'] = c['name']
            class_header = [a.name for a in self.db.MetaData.tables['Attribute'].c]
            class_values = dict(zip(class_header, [self.scope['class'], self.scope['domain']]))
            self.population['Class'].append(class_values)
            # for a in c['attributes']:
            #     attr_values = dict(
            #         zip(header['Attribute'], [a['name'], [self.scope['class'], self.scope['domain']]
            #             )
            #     )
            #     self.population['Attribute'].append(attr_values)

        print("Look at model")