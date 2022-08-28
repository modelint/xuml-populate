"""
xUML_class_model.py – Parses an xUML class model file
"""

import sys
from pathlib import Path
from class_model_dsl.parse.model_parser import ModelParser
from class_model_dsl.mp_exceptions import ModelParseError, MPIOException

class ClassModel:

    def __init__(self, path: Path):
        """Constructor"""
        self.xuml_model_path = path

        # Parse the model
        try:
            self.model = ModelParser(model_file_path=self.xuml_model_path, debug=False)
        except MPIOException as e:
            sys.exit(e)
        try:
            self.subsys = self.model.parse()
        except ModelParseError as e:
            sys.exit(e)