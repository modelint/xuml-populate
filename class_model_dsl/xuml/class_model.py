"""
class_model.py – Parses an xUML class model file
"""

import sys
import logging
from pathlib import Path
from class_model_dsl.parse.model_parser import ModelParser
from class_model_dsl.mp_exceptions import ModelParseError, MPIOException
from class_model_dsl.database.sm_meta_db import SMmetaDB, population
from class_model_dsl.populate.metaclass_headers import header

class ClassModel:

    def __init__(self, path: Path):
        """Constructor"""
        self.logger = logging.getLogger(__name__)
        self.xuml_model_path = path

        self.db = SMmetaDB(rebuild=True)

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


        # Get the domain name
        domain_name = self.subsystem.domain
        population['Domain'] = {'Name': domain_name}



        # Insert the domain
        domain_name = self.subsystem.domain
        domain_t = self.db.MetaData.tables['Domain']
        self.db.Connection.execute(domain_t.insert(), [{'Name': domain_name}])

        # Insert classes
        class_t = self.db.MetaData.tables['Class']
        attr_t = self.db.MetaData.tables['Attribute']
        class_relation = []
        attr_relation = []
        for c in self.subsystem.classes:
            class_values = dict(zip(header['Class'], [c['name'], domain_name]))
            class_relation.append(class_values)
            for a in c['attributes']:
                attr_values = dict(zip(header['Attribute'], [a['name'], c['name'], domain_name]))
                attr_relation.append(attr_values)
            self.db.Connection.execute(class_t.insert(), class_relation )
            self.db.Connection.execute(attr_t.insert(), attr_relation )

        print("Look at model")