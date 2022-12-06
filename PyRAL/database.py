"""
database.py -- TclRAL Database
"""
import logging
import tkinter

from typing import List, Dict
from PyRAL.rtypes import Attribute
from enum import Enum


class Mult(Enum):
    AT_LEAST_ONE = '+'
    EXACTLY_ONE = '1'
    ZERO_ONE_OR_MANY = '*'
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
        cls._logger.info(f"Adding class: {name}")
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
        # Join each attribute list into a string
        from_attr_str = "{" + ' '.join(from_attrs) + '}'
        to_attr_str = "{" + ' '.join(to_attrs) + '}'

        # Build a TclRAL command string
        cmd = f"relvar association {name} {from_relvar} {from_attr_str} {from_mult.value}" \
              f" {to_relvar} {to_attr_str} {to_mult.value}"

        # Execute the command and log the result
        cls.tclRAL.eval(cmd)
        result = cls.tclRAL.eval(f"relvar constraint info {name}")
        cls._logger.info(result)

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
        Example:
            relvar correlation C1 OWNERSHIP
                OwnerName + OWNER OwnerName
                DogName * DOG DogName

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
        # Join each attribute list into a string
        correl_a_attrs_str = "{" + ' '.join(correl_a_attrs) + '}'
        correl_b_attrs_str = "{" + ' '.join(correl_b_attrs) + '}'
        a_ref_attrs_str = "{" + ' '.join(a_ref_attrs) + '}'
        b_ref_attrs_str = "{" + ' '.join(b_ref_attrs) + '}'

        # Build a TclRAL command string
        cmd = f"relvar correlation {'-complete ' if complete else ''} {name} {correlation_relvar} " \
              f"{correl_a_attrs_str} {a_mult.value} {a_relvar} {a_ref_attrs_str} " \
              f"{correl_b_attrs_str} {b_mult.value} {b_relvar} {b_ref_attrs_str} "

        # Execute the command and log the result
        cls.tclRAL.eval(cmd)
        result = cls.tclRAL.eval(f"relvar constraint info {name}")
        cls._logger.info(result)

    @classmethod
    def create_partition(cls, name: str, super: str, super_attrs: List[str], subs: Dict[str, List[str]]):
        """
        relvar partition name super superAttrList
            sub1 sub1AttrList
            ...

        """
        super_attrs_str = '{' + ' '.join(super_attrs) + '}'
        all_subs = ""
        for subname, attrs in subs.items():
            all_subs += subname + ' ' + '{' + ' '.join(attrs) + '} '
        all_subs = all_subs[:-1]

        cmd = f"relvar partition {name} {super} {super_attrs_str} {all_subs}"
        cls.tclRAL.eval(cmd)
        result = cls.tclRAL.eval(f"relvar constraint info {name}")
        cls._logger.info(result)

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
