"""
sm_meta_db.py - Loads the existing Shlaer-Mellor Metamodel database
"""
import sys
import logging
import logging.config
from pathlib import Path
from sqlalchemy import create_engine, MetaData
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


population = { 'Domain': [], 'Class': [], 'Attributes': [] } # Database population to be generated

def Populate():
    """
    Populate the database with all the built relvars
    :return:
    """
    pass


def Create_relvars():
    """
    A relvar is a relational variable as defined by C.J. Date and Hugh Darwin.
    In the world of SQL it is effectively a table. Here we define all the relvars
    and then have the corresponding table schemas populated into the Sqlalchemy
    metadata.
    """
    from class_model_dsl.database import relvars
    SMmetaDB.Relvars = relvars.define(SMmetaDB)
    SMmetaDB.MetaData.create_all(SMmetaDB.Engine)


class SMmetaDB:
    """
    SM meta database containing all predefined metamodel data.

    Here we use Sqlalchemy to create the database engine and connection

        Attributes

        - File -- Local directory location of the sqlite3 database file
        - Metadata -- Sqlalchemy metadata
        - Connection -- Sqlalchemy database connection
        - Engine -- Sqlalchemy database engine
        - Relvars -- Dictionary of all relvar names and values (table names and row populations)
    """
    File = Path(__file__).parent / "sm_meta.db"
    LogFile = Path(__file__).parent / "db.log"
    MetaData = None
    Connection = None
    Engine = None
    Relvars = None

    def __init__(self, rebuild: bool):
        """
        Create the sqlite3 database using Sqlalchemy

        :param rebuild: During development this will usually be true.  For deployment it should be false.
        """
        self.logger = logging.getLogger(__name__)
        self.rebuild = rebuild

        if self.rebuild:  # DB rebuild requested
            self.logger.warning("Database rebuild requested, rebuilding SM meta database")
            # Start with a fresh database
            if SMmetaDB.File.exists():
                SMmetaDB.File.unlink()
        else:  # No rebuild requested
            if SMmetaDB.File.exists():
                self.logger.info("Using existing database")
            else:  # We're going to have to rebuild it anyway
                self.rebuild = True
                self.logger.info("No db file, rebuilding SM meta database")

        db_path_str = str(SMmetaDB.File)

        # Configure sql logger
        db_file_handler = logging.FileHandler(SMmetaDB.LogFile, 'w')
        # db_file_handler.setLevel(logging.DEBUG)
        dblogger = logging.getLogger('sqlalchemy.engine')
        dblogger.setLevel(logging.DEBUG)
        dblogger.addHandler(db_file_handler)
        dblogger.propagate = False  # To keep sql events from bleeding into the parser log

        SMmetaDB.Engine = create_engine(f'sqlite:///{db_path_str}', echo=False)
        SMmetaDB.Connection = SMmetaDB.Engine.connect()
        SMmetaDB.MetaData = MetaData(SMmetaDB.Engine)
        if self.rebuild:
            self.logger.info(f"Re-creating database file at: {db_path_str}")
            Create_relvars()
        else:
            # Just interrogate the existing database to get all the relvar/table names
            SMmetaDB.MetaData.reflect()


if __name__ == "__main__":
    #  Rebuild the database
    SMmetaDB()
