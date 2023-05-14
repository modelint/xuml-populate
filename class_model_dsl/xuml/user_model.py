"""
user_model.py – Parses a user model (aka M1 level model)

What we call the 'user model' is what the Object Management Group refers to as an M1 level model
to distinguish it from an M2 level model (metamododel) or an M0 level model which we just call a
user model or M1 population

For our purposes we will use the Elevator Management domain_name as one of our user / M1 test cases
"""

import sys
import logging
from pathlib import Path
from class_model_dsl.parse.model_parser import ModelParser
from class_model_dsl.parse.statemodel_parser import StateModelParser
from class_model_dsl.mp_exceptions import ModelParseError, MPIOException, MultipleDomainsException
from class_model_dsl.populate.domain import Domain
from class_model_dsl.populate.pop_types import Domain_i

class UserModel:
    """
    The command line specifies a package representing a Modeled Domain in some user directory.

    The package is a folder consisting of oen or more subsystem .xcm files and a single
    types yaml file.

    Once loaded, the model information is populated into an existing Metamodel database.
    """
    _logger = logging.getLogger(__name__)

    user_model_pkg = None
    user_model_path = None
    model_subsystem = {}  # Parsed subsystems, keyed by subsystem file name
    subsystem = None
    statemodels = {} # Parsed state models, keyed by name (class or rnum)
    statemodel = None
    model = None
    domain = None

    @classmethod
    def load(cls, user_model_pkg: Path):
        """

        :param user_model_pkg:
        """
        cls._logger.info(f"Processing user class models in : [{user_model_pkg}]")
        cls.user_model_pkg = user_model_pkg

        # Load the class model subsystems
        for subsys_cm_file in cls.user_model_pkg.glob("*.xcm"):
            cls._logger.info(f"Processing user subsystem class model file: [{subsys_cm_file}]")
            cls.parse_cm(cm_path=subsys_cm_file)
        # Load and parse the state models
        for sm_file in cls.user_model_pkg.glob("*.xsm"):
            cls._logger.info(f"Processing user subsystem state model file: [{sm_file}]")
            cls.parse_sm(sm_path=sm_file)
        cls.populate()

    @classmethod
    def parse_sm(cls, sm_path: Path):
        """
        Parse the state model

        :param sm_path:
        """
        sname = sm_path.stem
        try:
            cls.statemodel = StateModelParser(model_file_path=sm_path, debug=False)
        except MPIOException as e:
            sys.exit(e)
        try:
            cls.statemodels[sname] = cls.statemodel.parse()
        except ModelParseError as e:
            sys.exit(e)
        return cls.statemodels[sname]

    @classmethod
    def parse_cm(cls, cm_path: Path):
        """
        Parse the class model
        """
        sname = cm_path.stem # Subsystem name obtained from file name
        try:
            cls.model = ModelParser(model_file_path=cm_path, debug=False)
        except MPIOException as e:
            sys.exit(e)
        try:
            cls.model_subsystem[sname] = cls.model.parse()
        except ModelParseError as e:
            sys.exit(e)
        return cls.model_subsystem[sname]

    @classmethod
    def populate(cls):
        """Populate the database from the parsed input"""

        cls._logger.info("Populating the model")
        from PyRAL.database import Database # Metamodel load or creates has already initialized the DB session

        # Verify that only one domain_name has been specified
        # For now we are processing only a single domain_name.
        # Therefore each subsystem should specify the same domain_name. If not, we exit with an error.
        for sname, subsys in cls.model_subsystem.items():
            if not cls.domain:
                cls.domain = subsys.domain
            elif cls.domain != subsys.domain:
                cls._logger.error(f"Multiple domains: {cls.domain}, {subsys.domain}]")
                raise MultipleDomainsException

        # Populate the domain_name
        Domain.populate(mmdb=Database.tclRAL, package_path=cls.user_model_pkg,
                        domain=Domain_i(Name=cls.domain['name'], Alias=cls.domain['alias']),
                        subsystems=cls.model_subsystem, statemodels=cls.statemodels)