"""
user_model.py – Parses a user model (aka M1 level model)

What we call the 'user model' is what the Object Management Group refers to as an M1 level model
to distinguish it from an M2 level model (metamododel) or an M0 level model which we just call a
user model or M1 population

For our purposes we will use the Elevator Management domain as one of our user / M1 test cases
"""

# import sys
import logging
from pathlib import Path
# from class_model_dsl.xuml.metamodel import Metamodel
from class_model_dsl.parse.model_parser import ModelParser
from class_model_dsl.mp_exceptions import ModelParseError, MPIOException, MultipleDomainsException
from class_model_dsl.populate.domain import Domain
# from class_model_dsl.populate.lineage import Lineage
# from class_model_dsl.populate.attribute import ResolveAttrTypes
# from class_model_dsl.populate.mm_class import MMclass


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
    model = None
    domain = None

    @classmethod
    def load(cls, user_model_pkg: Path):
        """

        :param user_model_pkg:
        """
        cls._logger.info(f"Processing user class models in : [{user_model_pkg}]")
        cls.user_model_pkg = user_model_pkg
        for subsys_cm_file in cls.user_model_pkg.glob("*.xcm"):
            cls._logger.info(f"Processing user subsystem cm file: [{subsys_cm_file}]")
            cls.parse(cm_path=subsys_cm_file)
        cls.populate()
        # ResolveAttrTypes()

    @classmethod
    def parse(cls, cm_path):
        """
        Parse the model

        :return:
        """
        sname = cm_path.stem
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
        from PyRAL.database import Database

        # Insert classes
        cls._logger.info("Populating classes")
        for sname, subsys in cls.model_subsystem.items():
            # For now we are processing only a single domain.
            # Therefore each subsystem should specify the same domain. If not, we exit with an error.
            if not cls.domain:
                cls.domain = subsys.domain
            elif cls.domain != subsys.domain:
                cls._logger.error(f"Multiple domains: {cls.domain}, {subsys.domain}]")
                raise MultipleDomainsException

        Domain.populate(db=Database.tclRAL, domain=cls.domain, subsystems=cls.model_subsystem)
        pass

        # for c in cls.subsystem.classes:
        #     MMclass.populate(domain=domain, parse_data=c)

        # Insert relationships
        # self.logger.info("Populating relationships")
        # for r in self.parse_data.rels:
        #     Relationship(domain=self, subsys=s, parse_data=r)

        # self.domain = Domain(model=self, parse_data=self.subsystem)

        # for relvar_name, relation in self.population.items():
        #     t = SMmetaDB.Relvars[relvar_name]
        #     if relation:
        #         self.db.Connection.execute(t.insert(), relation)  # Sqlalchemy populates the table schema

        # cls._logger.info("Populating lineage")
        # Lineage(domain=self.domain)
