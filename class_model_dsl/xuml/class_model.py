"""
xUML_class_model.py – Parses an xUML class model file
"""

import sys
import logging
from pathlib import Path
from class_model_dsl.parse.model_parser import ModelParser
from class_model_dsl.mp_exceptions import ModelParseError, MPIOException
from class_model_dsl.database.sm_meta_db import SMmetaDB

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

        class_name = self.subsystem.classes[0]['name']
        class_t = self.db.MetaData.tables['Class']
        attr_t = self.db.MetaData.tables['Attribute']
        attr_name = 'Name'
        self.db.Connection.execute(class_t.insert(), [{'Name': class_name}])
        self.db.Connection.execute(attr_t.insert(), [{'Name': attr_name, 'Class': class_name }])

        print("Look at model")