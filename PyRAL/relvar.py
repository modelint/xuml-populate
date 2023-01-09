"""
relvar.py – Operations on relvars
"""

import logging
from tabulate import tabulate
import re
from typing import List, Dict, Any, TYPE_CHECKING
from PyRAL.rtypes import Attribute, Mult
from PyRAL.transaction import Transaction
from collections import namedtuple

if TYPE_CHECKING:
    from tkinter import Tk

class Relvar:
    """
    A relational variable (table)
    """
    _logger = logging.getLogger(__name__)

    @classmethod
    def create_relvar(cls, db: 'Tk', name: str, attrs: List[Attribute], ids: Dict[int, List[str]]):
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
        result = db.eval(cmd)
        cls._logger.info(f"Adding class: {name}")
        cls._logger.info(result)

    @classmethod
    def create_association(cls, db: 'Tk', name: str,
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
        db.eval(cmd)
        result = db.eval(f"relvar constraint info {name}")
        cls._logger.info(result)

    @classmethod
    def create_correlation(cls, db: 'Tk', name: str, correlation_relvar: str,
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

        :param db:  The TclRAL session
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
        # We need to reverse the a/b multiplicities since TclRAL considers multiplicty from the perspective
        # of the correlation relvar tuples rather than from the perspectives of the participating (non correlation)
        # relvar tuples. The latter approach matches the way SM modelers think.
        cmd = f"relvar correlation {'-complete ' if complete else ''} {name} {correlation_relvar} " \
              f"{correl_a_attrs_str} {b_mult.value} {a_relvar} {a_ref_attrs_str} " \
              f"{correl_b_attrs_str} {a_mult.value} {b_relvar} {b_ref_attrs_str} "

        # Execute the command and log the result
        db.eval(cmd)
        result = db.eval(f"relvar constraint info {name}")
        cls._logger.info(result)

    @classmethod
    def create_partition(cls, db: 'Tk', name: str,
                         superclass_name: str, super_attrs: List[str], subs: Dict[str, List[str]]):
        """
        relvar partition name superclass_name superAttrList
            sub1 sub1AttrList
            ...

        """
        super_attrs_str = '{' + ' '.join(super_attrs) + '}'
        all_subs = ""
        for subname, attrs in subs.items():
            all_subs += subname + ' ' + '{' + ' '.join(attrs) + '} '
        all_subs = all_subs[:-1]

        cmd = f"relvar partition {name} {superclass_name} {super_attrs_str} {all_subs}"
        db.eval(cmd)
        result = db.eval(f"relvar constraint info {name}")
        cls._logger.info(result)

    @classmethod
    def insert(cls, db: 'Tk', relvar: str, tuples: List[namedtuple]):
        """
        Creates an insert command and adds it to the open transaction.

        Does not actually execute the command.

        :return:
        """
        cmd = f"relvar insert {relvar} "
        for t in tuples:
            cmd += '{'
            instance_tuple = t._asdict()
            for k, v in instance_tuple.items():
                cmd += f"{k} {{{v}}} "  # Spaces are allowed in values
            cmd = cmd[:-1] + '} '
        cmd = cmd[:-1]
        Transaction.append_statement(statement=cmd)

        pass

    @classmethod
    def updateone(cls, db: 'Tk', relvar_name: str, id:Dict, update:Dict[str,Any]):
        """
        """
        id_str = ""
        for id_attr,id_val in id.items():
            id_str += f"{id_attr} {{{id_val}}} "
        update_str = ""
        for u_attr,u_val in update.items():
            update_str += u_attr + " {" + u_val + "}"
        cmd = f'relvar updateone {relvar_name} t {{{id_str}}} {{tuple update $t {update_str}}}'
        result = db.eval(cmd)


    @classmethod
    def population(cls, db: 'Tk', relvar: str):
        """

        :param db:
        :param relvar:
        :return:
        """
        result = db.eval(f"set {relvar}")
        # db.eval(f"puts ${relvar}")

    @classmethod
    def relformat(cls, db: 'Tk', relvar: str):
        """
        Prints a table of the specified relvar population.

        We obtain the value of the supplied relvar from TclRAL as a single string.
        We need to parse this string into attributes, types, and attribute values for
        each tuple so that we can display the data as a table using the imported tabulate
        module.

        :param db: The TclRAL session
        :param relvar: The value (a relation) of this variable is displayed
        """
        # The tcl set command returns a variable value, in this case a relvar
        result = db.eval(f"set {relvar}")

        # The result is a single, very long string, representing the value of the
        # relvar.

        # First we split the header from the body. The header consists of attribute and
        # type names surrounded by a pair of brackets like this: {attr1 type1 attr2 type2 ... }
        # followed by a space and then the body (all the tuples) also between a pair of braces.

        h, b = result.split('}', 1)  # Split at the first closing bracket to obtain header and body strings
        h = h.strip('{')  # Remove the open brace from the header string
        h_items = h.split(' ')  # There will be no spaces in any of the names, so we break on the space delimiter
        h_attrs = h_items[::2]  # Every even numbered item (0,2, ...) is an attribute name
        h_types = h_items[1::2]  # Every odd one is a type name
        deg = len(h_attrs)  # The degree of the relvar is the number of attributes (columns)

        # Now we process the body
        # Each tuple is surrounded by brackets so our first stop is to split them all out into distinct tuple strings
        body = b.split('} {')
        body[0] = body[0].lstrip(' {')  # Remove any preceding space or brackets from the first tuple
        # Each tuple alternates with the attribute name and the attribute value
        # We want to extract just the values to create the table rows
        # To complicate matters, values may contain spaces. TclRAL attribute names do not.
        # A multi-word value is surrounded by brackets
        # So you might see a tuple like this: Floor_height 32.6 Name {Lower lobby}
        # We need a regex component that will extract the bracketed space delimited values
        # As well as the non-bracketed single word values
        value_pattern = r"([{}<>\w ]*)"  # Grab a string of any combination of brackets, word characters and spaces
        # Now we build this component into an alternating pattern of attribute and value items
        # for the attributes in our relation header
        tuple_pattern = ""
        for a in h_attrs:
            tuple_pattern += f"{a} {value_pattern} "
        tuple_pattern = tuple_pattern.rstrip(' ')  # Removes the final trailing space
        # Now we can use the constructed tuple pattern regex to extract a list of values
        # from each row to match our attribute list order
        # Here we apply the tuple_pattern regex to each body row stripping the brackets from each value
        # and end up with a list of unbracketed body row values

        # For tabulate we need a list for the columns and a list of lists for the rows

        # Handle case where there are zero attributes
        b_rows = None  # Default assumption
        if deg == 0:
            h_attrs = ['<deg 0>']

        # Handle case where there are zero body tuples
        at_least_one_tuple = b.strip('{} ')  # Empty string if no tuples in body

        # Table with zero columns and one tuple
        # There cannot be many tuples since they would be duplicates, which are not allowed
        if deg == 0 and at_least_one_tuple:
            b_rows = [['<dee>']]  # Tabledee

        # There is at least one body tuple
        if at_least_one_tuple:
            if deg > 1:
                # More than one column and the regex match returns a convenient tuple in the zero element
                b_rows = [[f.strip('{}') for f in re.findall(tuple_pattern, row)[0]] for row in body]
            elif deg == 1:
                # If there is only one match (value), regex returns a string rather than a tuple
                # in the zero element. We need to embed this string in a list
                b_rows = [[re.findall(tuple_pattern, row)[0].strip('{}') for row in body]]
            # Either way, b_rows is a list of lists


        # Now we have what we need to generate a table
        print(f"\n-- {relvar} --")
        print(tabulate(b_rows, h_attrs, tablefmt="outline"))  # That last parameter chooses our table style