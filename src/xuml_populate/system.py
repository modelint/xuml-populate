""" system.py – Process all modeled domains within a system """

# System
import logging
from pathlib import Path
from contextlib import redirect_stdout

# Model Integration
from xcm_parser.class_model_parser import ClassModelParser
from xsm_parser.state_model_parser import StateModelParser
from op2_parser.op_parser import OpParser
from mtd_parser.method_parser import MethodParser
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
            # First make sure it is really a domain folder, or at least a folder
            # For example, on mac OS we sometimes trip on a .DS_Store file and, if so, we want to ignore it
            if domain_path.name.startswith('.'):
                _logger.warning(f"Path: {domain_path} is hidden -- skipping")
                continue

            if not domain_path.is_dir():
                _logger.warning(f"Path: {domain_path} is not a directory -- skipping")
                continue
            # File names may differ from the actual model element name due to case and delimiter differences
            # For example, the domain name `Elevator Management` may have the file name `elevator-management`
            # The domain name will be in the parsed content, but it is convenient to use the file names as keys
            # to organize our content dictionary since we these are immediately available
            domain_name = None  # Domain name is unknown until the class model is parsed
            _logger.info(f"Processing domain: [{domain_path}]")

            subsys_folders = [f for f in domain_path.iterdir() if f.is_dir()]
            for subsys_path in subsys_folders:

                # Process the class model for this subsystem
                # The class file name must match the subsystem folder name
                # Any other .xcm files will be ignored (only one class model recognized per subsystem)
                cm_file_name = subsys_path.stem + ".xcm"
                cm_path = subsys_path / "class-model" / cm_file_name
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

                # Get this subsystem name from the parse
                subsys_name = cm_parse.subsystem['name']

                # We add the subsystem dictionary to the system content for the current domain file name
                # inserting the class model parse
                self.content[domain_name]['subsystems'][subsys_name] = {
                    'class_model': cm_parse, 'methods': {}, 'state_models': {}, 'external': {}
                }

                # Load and parse all the methods for the current subsystem folder
                method_path = subsys_path / "methods"
                if method_path.is_dir():
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
                else:
                    _logger.info("No method dir")

                # Load and parse the current subsystem's state models (state machines)
                sm_path = subsys_path / "state-machines"
                if sm_path.is_dir():
                    for sm_file in sm_path.glob("*.xsm"):
                        sm_name = sm_file.stem
                        _logger.info(f"Processing state model: [{sm_file}]")
                        # Parse the state model
                        sm_parse = StateModelParser.parse_file(file_input=sm_file, debug=False)
                        self.content[domain_name]['subsystems'][subsys_name]['state_models'][sm_name] = sm_parse
                else:
                    _logger.info("No state-machines dir")

                # Load and parse the external entity operations
                ext_path = subsys_path / "external"
                if ext_path.is_dir():
                    for ee_path in ext_path.iterdir():
                        ee_name = ee_path.name
                        self.content[domain_name]['subsystems'][subsys_name]['external'][ee_name] = {}
                        for op_file in ee_path.glob("*.op"):
                            op_name = op_file.stem
                            _logger.info(f"Processing ee operation: [{op_file}]")
                            op_parse = OpParser.parse_file(file_input=op_file, debug=False)
                            self.content[domain_name]['subsystems'][subsys_name]['external'][ee_name][op_name] = op_parse
                else:
                    _logger.info("No external dir")

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
        saved_mmdb_name = f"mmdb_{self.name}.ral"
        Database.save(db=mmdb, fname=saved_mmdb_name)

        # Output a text file of the populated mmdb
        mmdb_printout = f"mmdb_{self.name}.txt"
        with open(mmdb_printout, 'w') as f:
            with redirect_stdout(f):
                Relvar.printall(db=mmdb)
