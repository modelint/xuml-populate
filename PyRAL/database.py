"""
database.py -- TclRAL Database
"""
import logging
import tkinter

from typing import List, Dict
from PyRAL.rtypes import Attribute
from enum import Enum


class Mult(Enum):
    AT_LEAST_ONE = '+',
    EXACTLY_ONE = '1',
    ZERO_ONE_OR_MANY = '*',
    ZERO_OR_ONE = '?'


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
        for inum, attrs in ids.items():
            id_const += '{'
            for a in attrs:
                id_const += a.replace(' ', '_') + ' '
            id_const = id_const[:-1] + '} '
        id_const = id_const[:-1]

        cmd = f"relvar create {name} {header} {id_const}"
        result = cls.tclRAL.eval(cmd)
        cls._logger.info(result)

    @classmethod
    def create_association(cls, name: str,
                           from_relvar: str, from_attrs: List[str], from_mult: Mult,
                           to_relvar: str, to_attrs: List[str], to_mult: Mult,
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
        cls._logger.info(result)
        # relvar association R1 \
        # Subsystem {First_element_number Domain} 1 \
        # Domain_Partition {Number Domain} 1
        pass

    @classmethod
    def create_correlation(cls, name: str, correlation_relvar: str,
                           correl_a_attrs: List[str], a_mult: Mult, a_relvar: str, a_ref_attrs: List[str],
                           correl_b_attrs: List[str], b_mult: Mult, b_relvar: str, b_ref_attrs: List[str],
                           complete: bool = False):
        """
        TclRAL syntax from man page
        relvar correlation ?-complete? name correlRelvar
             correlAttrListA refToSpecA refToRelvarA refToAttrListA
             correlAttrListB refToSpecB refToRelvarB refToAttrListB

        :param name: Name of the correlation
        :param correlation_relvar: Name of the relvar holding the correlation
        :param correl_a_attrs: Attrs in correlation relvar referencing a-side relvar
        :param a_mult: Multiplicity on the a-side relvar
        :param a_relvar: Name of the a-side relvar
        :param a_ref_attrs: Attrs in the a-side relvar referencd by the correlation
        :param correl_b_attrs: Attrs in correlation relvar referencing b-side relvar
        :param b_mult: Multiplicity on the b-side relvar
        :param b_relvar: Name of the b-side relvar
        :param b_ref_attrs: Attrs in the b-side relvar referencd by the correlation
        :param complete: True implies the cardinality of correlRelvar must equal the product of the cardinality of
            refToRelvarA and refToRelvarB. If False, correlRelvar is allowed to have a subset of the Cartesian product
            of the references.
        :return:
        """
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
