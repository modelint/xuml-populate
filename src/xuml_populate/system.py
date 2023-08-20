""" system.py – Process all modeled domains within a system """

import logging
from pathlib import Path
from xcm_parser.class_model_parser import ClassModelParser
from xsm_parser.state_model_parser import StateModelParser
from mtd_parser.method_parser import MethodParser
# from xuml_populate.mp_exceptions import MultipleDomainsException
# from xuml_populate.populate.domain import Domain
# from xuml_populate.populate.mmclass_nt import Domain_i

_mmdb_fname = "mmdb.txt"

class System:
    """
    The command line specifies a package representing a System.

    The package is a folder consisting of one or more domains and each domain has a structure
    as specified in the readme file.
    """
    _logger = logging.getLogger(__name__)

    content = {}
    mmdb_path = Path(__file__).parent / "populate" / _mmdb_fname  # Path to src folder
    system_path = None
    model_subsystem = {}  # Parsed subsystems, keyed by subsystem file name
    subsystem = None
    method = None
    methods = {}  # Parsed methods, keyed by class
    statemodels = {}  # Parsed state models, keyed by name (class or rnum)
    statemodel = None
    model = None
    domain = None

    @classmethod
    def load(cls, system_pkg_path: Path):
        """
        Parse and otherwise process the contents of each modeled domain in the system.
        Then populate the content of each domain into the metamodel database.

        :param system_pkg_path:  The path to the system package
        """
        cls._logger.info(f"Processing system: [{system_pkg_path}]")
        cls.system_path = system_pkg_path

        for domain_path in cls.system_path.iterdir():
            domain_fname = domain_path.stem
            cls._logger.info(f"Processing domain: [{domain_path}]")
            # Populate each subsystem
            subsys_folders = [f for f in domain_path.iterdir() if f.is_dir()]
            for subsys_path in subsys_folders:
                subsys_fname = subsys_path.stem
                # The class file name must match the subsystem folder name
                # Any other .xcm files will be ignored (only one recognized per subsystem)
                cm_file_name = subsys_path.stem + ".xcm"
                cm_path = subsys_path / cm_file_name
                cls._logger.info(f"Processing class model: [{cm_path}]")
                cm_parse = ClassModelParser.parse_file(file_input=cm_path, debug=False)
                # We initialize the subsystem dictionary with the class model
                cls.content[domain_fname] = {
                    # subystem parses
                    subsys_fname: {'class_model': cm_parse, 'methods': {}, 'state_models': {}}
                }

                # Load and parse all the methods
                method_path = subsys_path / "methods"
                class_folders = [f for f in method_path.iterdir() if f.is_dir()]
                for class_folder in class_folders:
                    for method_file in class_folder.glob("*.mtd"):
                        method_name = method_file.stem
                        cls._logger.info(f"Processing method: [{method_file}]")
                        mtd_parse = MethodParser.parse_file(method_file, debug=False)
                        cls.content[domain_fname][subsys_fname]['methods'][method_name] = mtd_parse

                # Load and parse the subsystem state machines
                sm_path = subsys_path / "state-machines"
                for sm_file in sm_path.glob("*.xsm"):
                    sm_name = sm_file.stem
                    cls._logger.info(f"Processing state model: [{sm_file}]")
                    sm_parse = StateModelParser.parse_file(file_input=sm_file, debug=False)
                    cls.content[domain_fname][subsys_fname]['state_models'][sm_name] = sm_parse

        cls.populate()

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