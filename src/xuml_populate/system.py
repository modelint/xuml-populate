""" system.py – Process all modeled domains within a system """

import logging
from pathlib import Path
import yaml
from xcm_parser.class_model_parser import ClassModelParser
from xsm_parser.state_model_parser import StateModelParser
from mtd_parser.method_parser import MethodParser
from xuml_populate.populate.domain import Domain

_mmdb_fname = "mmdb.txt"

class System:
    """
    The command line specifies a package representing a System. The organization of this package is defined
    in the readme file.

    We need to descend through that package loading and parsing all the files for the entire system.

    We then proceed to populate each modeled domain in the repository.
    """
    _logger = logging.getLogger(__name__)

    content = {}  # Parsed content for all files in the system package
    mmdb_path = Path(__file__).parent / "populate" / _mmdb_fname  # Path to the serialized repository db

    @classmethod
    def load(cls, system_path: Path):
        """
        Parse and otherwise process the contents of each modeled domain in the system.
        Then populate the content of each domain into the metamodel database.

        :param system_path:  The path to the system package
        """
        cls._logger.info(f"Processing system: [{system_path}]")

        # Process each domain folder in the system package
        for domain_path in system_path.iterdir():
            # File names may differ from the actual model element name due to case and delimiter differences
            # For example, the domain name `Elevator Management` may have the file name `elevator-management`
            # The domain name will be in the parsed content, but it is convenient to use the file names as keys
            # to organize our content dictionary since we these are immediately available
            domain_name = None  # Domain name is unknown until the class model is parsed
            domain_alias = None
            cls._logger.info(f"Processing domain: [{domain_path}]")

            # Populate each subsystem of this domain
            subsys_folders = [f for f in domain_path.iterdir() if f.is_dir()]
            for subsys_path in subsys_folders:

                # Process the class model for this subsystem
                # The class file name must match the subsystem folder name
                # Any other .xcm files will be ignored (only one class model recognized per subsystem)
                cm_file_name = subsys_path.stem + ".xcm"
                cm_path = subsys_path / cm_file_name
                cls._logger.info(f"Processing class model: [{cm_path}]")
                # Parse the class model
                cm_parse = ClassModelParser.parse_file(file_input=cm_path, debug=False)

                # If this is the first subsystem in the domain, get the domain name from the cm parse
                # domain will be None on the first subsystem
                if not domain_name:
                    domain_name = cm_parse.domain['name']
                    domain_alias = cm_parse.domain['alias']
                    # Create dictionary key for domain content
                    cls.content[domain_name] = {'alias': domain_alias, 'subsystems': {} }

                    # Parse the domain's types.yaml file with all of the domain specific types (data types)
                    # Load domain_name specific types
                    try:
                        with open(domain_path / "types.yaml", 'r') as file:
                            cls.content[domain_name]['types'] = yaml.safe_load(file)
                    except FileNotFoundError:
                        cls._logger.error(f"No types.yaml file found for domain at: {domain_path}")

                # Get this subsystem name from the parse
                subsys_name = cm_parse.subsystem['name']

                # We add the subsystem dictionary to the system content for the current domain file name
                # inserting the class model parse
                cls.content[domain_name]['subsystems'][subsys_name] = {
                    'class_model': cm_parse, 'methods': {}, 'state_models': {}
                }

                # Load and parse all the methods for the current subsystem folder
                method_path = subsys_path / "methods"
                # Find all class folders in the current subsystem methods directory
                class_folders = [f for f in method_path.iterdir() if f.is_dir()]
                for class_folder in class_folders:
                    # Process each method file in this class folder
                    for method_file in class_folder.glob("*.mtd"):
                        method_name = method_file.stem
                        cls._logger.info(f"Processing method: [{method_file}]")
                        # Parse the method file and insert it in the subsystem subsys_parse
                        mtd_parse = MethodParser.parse_file(method_file, debug=False)
                        cls.content[domain_name]['subsystems'][subsys_name]['methods'][method_name] = mtd_parse

                # Load and parse the current subsystem's state models (state machines)
                sm_path = subsys_path / "state-machines"
                for sm_file in sm_path.glob("*.xsm"):
                    sm_name = sm_file.stem
                    cls._logger.info(f"Processing state model: [{sm_file}]")
                    # Parse the state model
                    sm_parse = StateModelParser.parse_file(file_input=sm_file, debug=False)
                    cls.content[domain_name]['subsystems'][subsys_name]['state_models'][sm_name] = sm_parse

                # TODO load the external entity operations

        cls.populate()

    @classmethod
    def populate(cls):
        """Populate the database from the parsed input"""

        # Initiate a connection to the TclRAL database
        from pyral.database import Database  # Metamodel load or creates has already initialized the DB session
        cls._logger.info("Initializing TclRAL database connection")
        mmdb = Database.init()

        # Start with an empty metamodel repository
        cls._logger.info("Loading Blueprint MBSE metamodel repository schema")
        # We don't pass in the mmdb value since, at present, there is only one db open at a time
        # And PyRAL already has the connection open
        Database.load(cls.mmdb_path)

        # Populate each domain into the metamodel db
        for domain_name, domain_parse in cls.content.items():
            Domain.populate(mmdb, domain_name, domain_parse)
