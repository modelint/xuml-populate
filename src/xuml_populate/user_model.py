"""
user_model.py – Parses a user model (aka M1 level model)

What we call the 'user model' is what the Object Management Group refers to as an M1 level model
to distinguish it from an M2 level model (metamododel) or an M0 level model which we just call a
user model or M1 population

For our purposes we will use the elevator Management domain_name as one of our user / M1 test cases
"""

import logging
from pathlib import Path
from xcm_parser.class_model_parser import ClassModelParser
from xsm_parser.state_model_parser import StateModelParser
from mtd_parser.method_parser import MethodParser
# from xuml_populate.mp_exceptions import MultipleDomainsException
# from xuml_populate.populate.domain import Domain
# from xuml_populate.populate.mmclass_nt import Domain_i

_mmdb_fname = "mmdb.txt"

class UserModel:
    """
    The command line specifies a package representing a Modeled Domain in some user directory.

    The package is a folder consisting of oen or more subsystem .xcm files and a single
    types yaml file.

    Once loaded, the model information is populated into an existing Metamodel database.
    """
    _logger = logging.getLogger(__name__)

    mmdb_path = Path(__file__).parent / "populate" / _mmdb_fname  # Path to src folder
    domain_path = None
    model_subsystem = {}  # Parsed subsystems, keyed by subsystem file name
    subsystem = None
    method = None
    methods = {}  # Parsed methods, keyed by class
    statemodels = {}  # Parsed state models, keyed by name (class or rnum)
    statemodel = None
    model = None
    domain = None

    @classmethod
    def load(cls, domain_pkg_path: Path):
        """
        A user model is defined, for now, as a single domain within a system.
        The domain defines a set of types (data types) and a subsystems folder
        containing one or more subsystems.

        Each subsystem consists of classes, state machines, operations, and
        methods.

        Here we load the entire contents of the specified domain package.

        :param domain_pkg_path:  The path to the user domain model
        """
        cls._logger.info(f"Processing user class models in : [{domain_pkg_path}]")
        cls.domain_path = domain_pkg_path

        for d in cls.domain_path.iterdir():
            # Populate each subsystem
            subsys_folders = [s for s in d.iterdir() if s.is_dir()]
            for s in subsys_folders:
                cm_file_name = s.stem + ".xcm"
                cm_file = s / cm_file_name
                cls._logger.info(f"Processing class model file: [{cm_file}]")
                cls.parse_cm(cm_path=cm_file)

                # Load and parse all the methods
                method_path = s / "methods"
                for class_dir in method_path.iterdir():
                    for method_file in class_dir.glob("*.mtd"):
                        method_name = method_file.stem
                        cls._logger.info(f"Processing state model file: [{method_file}]")
                        cls.methods[method_name] = MethodParser.parse_file(method_file, debug=False)

                # Load and parse the subsystem state machines
                sm_path = s / "state-machines"
                for sm_file in sm_path.glob("*.xsm"):
                    cls._logger.info(f"Processing method file: [{sm_file}]")
                    cls.parse_sm(sm_path=sm_file)

        cls.populate()

    @classmethod
    def parse_sm(cls, sm_path: Path):
        """
        Parse the state model

        :param sm_path:
        """
        sname = sm_path.stem
        cls.statemodels[sname] = StateModelParser.parse_file(file_input=sm_path, debug=False)
        return cls.statemodels[sname]

    @classmethod
    def parse_cm(cls, cm_path: Path):
        """
        Parse the class model
        """
        sname = cm_path.stem # Subsystem name obtained from file name
        cls.model_subsystem[sname] = ClassModelParser.parse_file(file_input=cm_path, debug=False)
        return cls.model_subsystem[sname]

    @classmethod
    def populate(cls):
        """Populate the database from the parsed input"""

        cls._logger.info("Populating the model")
        from pyral.database import Database  # Metamodel load or creates has already initialized the DB session
        cls.db = Database.init()
        Database.load(cls.mmdb_path)
        # For now there is only one db so the db returned from the init() call
        # is the same as the one stored in the Database singleton (no need to pass in db to the load method)
        # TODO: Update PyRAL to manage multiple db's, or at least pretend to

        for sname, subsys in cls.model_subsystem.items():
            if not cls.domain:
                cls.domain = subsys.domain
            elif cls.domain != subsys.domain:
                cls._logger.error(f"Multiple domains: {cls.domain}, {subsys.domain}]")
                raise MultipleDomainsException

        # Populate the domain_name
        Domain.populate(mmdb=Database.tclRAL, domain_path=cls.domain_path,
                        domain=Domain_i(Name=cls.domain['name'], Alias=cls.domain['alias']),
                        subsystems=cls.model_subsystem, statemodels=cls.statemodels)