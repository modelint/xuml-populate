"""
database.py -- TclRAL Database
"""
import logging
import tkinter

from typing import List, Dict
from PyRAL.rtypes import Attribute


class Database:
    """
    Proxy for a tclRAL database.

    First we must initiate the connection with an optionally specified database.
    If none is specified, a new in memory database may be created

    """
    _logger = logging.getLogger(__name__)
    tclRAL = None  # Tcl interpreter

    @classmethod
    def init(cls, db_path=None):
        """
        Get a tcl interpreter and run a script in it that loads up TclRAL
        :return:
        """
        cls.tclRAL = tkinter.Tcl()  # Got tcl interpreter
        # Load TclRAL into that interpreter
        cls.tclRAL.eval("source PyRAL/tcl_scripts/init_TclRAL.tcl")
        cls._logger.info("TclRAL initiated")

        if db_path:
            # TODO: Have TclRAL load the db from the specified path
            pass

    @classmethod
    def create_relvar(cls, name: str, attrs: List[Attribute], ids: Dict[int, List[str]]):
        """
        Compose a TclRAL relvar create commmand from the supplied class
        definition.
        """
        # relvar create PUPPY {PuppyName string Dame string Sire string} {attr names} ...
        header = ""
        for a in attrs:
            header += a.name.replace(' ', '_') + ' ' + a.type.replace(' ', '_') + ' '
        header = f"{{{header[:-1]}}}"

        id_const = ""
        for inum,attrs in ids.items():
            id_const += '{'
            for a in attrs:
                id_const += a.replace(' ', '_') + ' '
            id_const = id_const[:-1] + '} '
        id_const = id_const[:-1]

        cmd = f"relvar create {name} {header} {id_const}"
        result = cls.tclRAL.eval(cmd)
        print(result)

    @classmethod
    def create_association(cls, name: str,
                           from_relvar: str, from_attrs: List[str], from_mult: str,
                           to_relvar: str, to_attrs: List[str], to_mult: str,
                           ):
        """
        Create a TclRAL association

        :return:
        """
        from_attr_str = "{"
        for a in from_attrs:
            from_attr_str += a + ' '
        from_attr_str = from_attr_str[:-1] + "}"

        to_attr_str = "{"
        for a in to_attrs:
            to_attr_str += a + ' '
        to_attr_str = to_attr_str[:-1] + "}"
        cmd = f"relvar association {name} {from_relvar} {from_attr_str} {from_mult}" \
              f" {to_relvar} {to_attr_str} {to_mult}"
        cls.tclRAL.eval(cmd)
        result = cls.tclRAL.eval("relvar constraint info R20")
        print(result)
        # relvar association R1 \
        # Subsystem {First_element_number Domain} 1 \
        # Domain_Partition {Number Domain} 1
        pass

    @classmethod
    def create_correlation(cls):
        pass

    @classmethod
    def create_partition(cls):
        pass

    @classmethod
    def populateSchema(cls):
        """
        Invoke whatever method does this. Not sure yet how to specify
        """
        pass

    @classmethod
    def save(cls, dbname):
        """
        Invoke whatever method does this. Not sure yet how to specify
        """
        pass