"""
xUML_class_model.py – Parses an xUML class model file
"""

import sys
import logging
from pathlib import Path
from class_model_dsl.parse.model_parser import ModelParser
from class_model_dsl.mp_exceptions import ModelParseError, MPIOException

class ClassModel:

    def __init__(self, path: Path):
        """Constructor"""
        self.logger = logging.getLogger(__name__)
        self.xuml_model_path = path

        self.logger.info("Parsing the model")
        # Parse the model
        try:
            self.model = ModelParser(model_file_path=self.xuml_model_path, debug=False)
        except MPIOException as e:
            sys.exit(e)
        try:
            self.metadata = self.model.parse()
        except ModelParseError as e:
            sys.exit(e)