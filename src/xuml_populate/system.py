""" system.py – Process all modeled domains within a system """

# System
import logging
from pathlib import Path
import yaml

# Model Integration
from xcm_parser.class_model_parser import ClassModelParser
from xsm_parser.state_model_parser import StateModelParser
from op2_parser.op_parser import OpParser
from mtd_parser.method_parser import MethodParser
from pyral.database import Database
from pyral.relvar import Relvar

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.domain import Domain
from xuml_populate.populate.mmclass_nt import System_i

_mmdb_fname = f"{mmdb}.ral"
_logger = logging.getLogger(__name__)


class System:
    """
    The command line specifies a package representing a System. The organization of this package is defined
    in the readme file.

    We need to descend through that package loading and parsing all the files for the entire system.

    We then proceed to populate each modeled domain in the repository.
    """

    def __init__(self, name: str, system_path: Path, parse_actions: bool = False, display=False):
        """
        Parse and otherwise process the contents of each modeled domain in the system.
        Then populate the content of each domain into the metamodel database.

        :param system_path: The path to the system package
        :param parse_actions: If true, all action text is parsed and populated into the metamodel,
        otherwise it is just kept as text
        """
        _logger.info(f"Processing system: [{system_path}]")

        self.name = name
        self.parse_actions = parse_actions
        self.content = {}  # Parsed content for all files in the system package
        self.mmdb_path = Path(__file__).parent / "populate" / _mmdb_fname  # Path to the serialized repository db
        self.system_name = system_path.stem.title()
        self.display=display

        # Process each domain folder in the system package
        for domain_path in system_path.iterdir():
            # File names may differ from the actual model element name due to case and delimiter differences
            # For example, the domain name `Elevator Management` may have the file name `elevator-management`
            # The domain name will be in the parsed content, but it is convenient to use the file names as keys
            # to organize our content dictionary since we these are immediately available
            domain_name = None  # Domain name is unknown until the class model is parsed
            _logger.info(f"Processing domain: [{domain_path}]")

            # Populate each subsystem of this domain
            subsys_folders = [f for f in domain_path.iterdir() if f.is_dir()]
            for subsys_path in subsys_folders:

                # Process the class model for this subsystem
                # The class file name must match the subsystem folder name
                # Any other .xcm files will be ignored (only one class model recognized per subsystem)
                cm_file_name = subsys_path.stem + ".xcm"
                cm_path = subsys_path / cm_file_name
                _logger.info(f"Processing class model: [{cm_path}]")
                # Parse the class model
                cm_parse = ClassModelParser.parse_file(file_input=cm_path, debug=False)

                # If this is the first subsystem in the domain, get the domain name from the cm parse
                # domain will be None on the first subsystem
                if not domain_name:
                    domain_name = cm_parse.domain['name']
                    domain_alias = cm_parse.domain['alias']
                    # Create dictionary key for domain content
                    self.content[domain_name] = {'alias': domain_alias, 'subsystems': {}}

                    # Parse the domain's types.yaml file with all of the domain specific types (data types)
                    # Load domain specific types
                    try:
                        with open(domain_path / "types.yaml", 'r') as file:
                            self.content[domain_name]['types'] = yaml.safe_load(file)
                    except FileNotFoundError:
                        _logger.error(f"No types.yaml file found for domain at: {domain_path}")

                # Get this subsystem name from the parse
                subsys_name = cm_parse.subsystem['name']

                # We add the subsystem dictionary to the system content for the current domain file name
                # inserting the class model parse
                self.content[domain_name]['subsystems'][subsys_name] = {
                    'class_model': cm_parse, 'methods': {}, 'state_models': {}, 'external': {}
                }

                # Load and parse all the methods for the current subsystem folder
                method_path = subsys_path / "methods"
                # Find all class folders in the current subsystem methods directory
                class_folders = [f for f in method_path.iterdir() if f.is_dir()]
                for class_folder in class_folders:
                    # Process each method file in this class folder
                    for method_file in class_folder.glob("*.mtd"):
                        method_name = method_file.stem
                        _logger.info(f"Processing method: [{method_file}]")
                        # Parse the method file and insert it in the subsystem subsys_parse
                        mtd_parse = MethodParser.parse_file(method_file, debug=False)
                        self.content[domain_name]['subsystems'][subsys_name]['methods'][method_name] = mtd_parse

                # Load and parse the current subsystem's state models (state machines)
                sm_path = subsys_path / "state-machines"
                for sm_file in sm_path.glob("*.xsm"):
                    sm_name = sm_file.stem
                    _logger.info(f"Processing state model: [{sm_file}]")
                    # Parse the state model
                    sm_parse = StateModelParser.parse_file(file_input=sm_file, debug=False)
                    self.content[domain_name]['subsystems'][subsys_name]['state_models'][sm_name] = sm_parse

                # Load and parse the external entity operations
                ext_path = subsys_path / "external"
                for ee_path in ext_path.iterdir():
                    ee_name = ee_path.name
                    self.content[domain_name]['subsystems'][subsys_name]['external'][ee_name] = {}
                    for op_file in ee_path.glob("*.op"):
                        op_name = op_file.stem
                        _logger.info(f"Processing ee operation: [{op_file}]")
                        op_parse = OpParser.parse_file(file_input=op_file, debug=False)
                        self.content[domain_name]['subsystems'][subsys_name]['external'][ee_name][op_name] = op_parse

        self.populate()

    def populate(self):
        """Populate the database from the parsed input"""

        # Initiate a connection to the TclRAL database
        from pyral.database import Database  # Metamodel load or creates has already initialized the DB session
        _logger.info("Initializing TclRAL database connection")
        Database.open_session(mmdb)

        # Start with an empty metamodel repository
        _logger.info("Loading Blueprint MBSE metamodel repository schema")
        Database.load(db=mmdb, fname=str(self.mmdb_path))

        # Populate the single instance System class
        Relvar.insert(db=mmdb, relvar='System', tuples=[
            System_i(Name=self.system_name),
        ])

        # Populate each domain into the metamodel db
        for domain_name, domain_parse in self.content.items():
            Domain(domain=domain_name, content=domain_parse, parse_actions=self.parse_actions, display=self.display)

        # Save the populated metamodel
        Database.save(db=mmdb, fname=f"mmdb_{self.name}.ral")
