"""
relation.py – Operations on relations
"""

import logging
import re
from tabulate import tabulate
from typing import List, Dict, TYPE_CHECKING
from PyRAL.rtypes import RelationValue
from collections import namedtuple

if TYPE_CHECKING:
    from tkinter import Tk

# If we want to apply successive (nested) operations in TclRAL we need to have the result
# of each TclRAL command saved in tcl variable. So each time we execute a command that produces
# a relation result we save it. The variable name is chosen so that it shouldn't conflict with
# any user relvars. Do not ever use the name below as one of your user relvars!
# For any given command, if no relvar is specified, the previous relation result is assumed
# to be the input.
_relation = r'^relation'  # Name of the latest relation result


class Relation:
    """
    A relational value
    """
    _logger = logging.getLogger(__name__)

    @classmethod
    def build_select_expr(cls, selection: str) -> str:
        """
        Convert a Scrall style select expression to an equivalent Tcl string match expression

        For now we only support an and'ed list of direct string matches in the format:

           attr1:str1, attr2:str2, ...

        With the assumption that we would like to select each tuple where

        attr1 == str1 AND attr2 == str2 ...

        We'll convert this to a Tcl expression like this:

        {[string match str1 $attr1] && [string match str2 $attr2] ...}

        Note that this only works for the TclRAL relation restrictwith command and not the
        relation restrict command. But that should suffice for our purposes

        Once our Scrall parser is ready, we can expand the functionality further

        :param selection:  The Scrall style select expression
        :return: The Tcl expression
        """
        # Parse out matches on comma delimiter as a list of strings
        match_strings = selection.split(',')
        # Break each match on the ':' into attr and value as a dictionary
        attr_vals = {a[0].strip(): a[1].strip() for a in [m.split(':') for m in match_strings]}
        # Now build the selection expression from each dictionary item
        sexpr = "{"  # Selection expression is surrounded by brackets
        for attribute,value in attr_vals.items():
            # We AND them all together with the && tcl operator
            sexpr += f"[string match {{{value}}} ${attribute}] && "
        # Remove the trailing && and return the complete selection expression
        return sexpr.rstrip(' &&') + "}"


    @classmethod
    def restrict(cls, db: 'Tk', relation: str, restriction: str) -> str:
        """
        Perform a restriction and return the result
        """
        # Parse the restriction expression
        # Split out matches on comma delimiter as a list of strings
        match_strings = restriction.split(',')
        # Break each match on the ':' into attr and value as a dictionary
        attr_vals = {a[0].strip(): a[1].strip() for a in [m.split(':') for m in match_strings]}
        # Now build the selection expression from each dictionary item
        rexpr = "{"  # Selection expression is surrounded by brackets
        for attribute,value in attr_vals.items():
            # We AND them all together with the && tcl operator
            rexpr += f"[string match {{{value}}} [tuple extract $t {attribute}]] && " # For use with restrict command
            # rexpr += f"[string match {{{value}}} ${attribute}] && " # For use with restrictwith command
        # Remove the trailing && and return the complete selection expression
        rexpr = rexpr.rstrip(' &&') + "}"

        # Add it to the restrictwith command and evaluate
        # result = db.eval("relation restrict $Attribute a {[string match <unresolved> [tuple extract $a Type]]}")
        cmd = f"set {_relation} [relation restrict ${relation} t {rexpr}]"
        result = db.eval(cmd)
        cls.relformat(db=db, relation=result)
        return result

    @classmethod
    def project(cls, db: 'Tk', attributes: List[str], relation: str=_relation) -> str:
        """
        Project attributes over relation

        :param attributes:
        :param db:
        :param relation:
        :return:
        """
        projection = ""
        for a in attributes:
            projection += f"{a} "
        cmd = f'set {_relation} [relation project ${{{relation}}} {projection.strip()}]'
        result = db.eval(cmd)
        cls.relformat(db=db, relation=result)
        return result

    @classmethod
    def makedict(cls, relation: str) -> RelationValue:
        """

        :param relation:
        :return:
        """
        h, b = relation.split('}', 1)  # Split at the first closing bracket to obtain header and body strings
        h = h.strip('{')  # Remove the open brace from the header string
        h_items = h.split(' ')  # There will be no spaces in any of the names, so we break on the space delimiter
        h_attrs = h_items[::2]  # Every even numbered item (0,2, ...) is an attribute name
        h_types = h_items[1::2]  # Every odd one is a type name
        deg = len(h_attrs)  # The degree of the relation is the number of attributes (columns)

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

        # Handle case where there are zero body tuples
        at_least_one_tuple = b.strip('{} ')  # Empty string if no tuples in body

        # There is at least one body tuple
        if at_least_one_tuple:
            if deg > 1:
                # More than one column and the regex match returns a convenient tuple in the zero element
                # b_rows = [for row in body]
                b_rows = [[f.strip('{}') for f in re.findall(tuple_pattern, row)[0]] for row in body]
            elif deg == 1:
                # If there is only one match (value), regex returns a string rather than a tuple
                # in the zero element. We need to embed this string in a list
                b_rows = [[re.findall(tuple_pattern, row)[0].strip('{}') for row in body]]
            # Either way, b_rows is a list of lists

        rbody = [dict(zip(h_attrs, r)) for r in b_rows]
        rval = RelationValue(header=h_attrs, body=rbody)
        return rval



    @classmethod
    def relformat(cls, db: 'Tk', relation: str):
        """
        Prints a table of the specified relation population.

        We obtain the value of the supplied relation from TclRAL as a single string.
        We need to parse this string into attributes, types, and attribute values for
        each tuple so that we can display the data as a table using the imported tabulate
        module.

        :param db: The TclRAL session
        :param relation: The value (a relation) of this variable is displayed
        """
        # The tcl set command returns a variable value, in this case a relation
        # result = db.eval(f"set {relation}")

        # The result is a single, very long string, representing the value of the
        # relation.

        # First we split the header from the body. The header consists of attribute and
        # type names surrounded by a pair of brackets like this: {attr1 type1 attr2 type2 ... }
        # followed by a space and then the body (all the tuples) also between a pair of braces.

        h, b = relation.split('}', 1)  # Split at the first closing bracket to obtain header and body strings
        h = h.strip('{')  # Remove the open brace from the header string
        h_items = h.split(' ')  # There will be no spaces in any of the names, so we break on the space delimiter
        h_attrs = h_items[::2]  # Every even numbered item (0,2, ...) is an attribute name
        h_types = h_items[1::2]  # Every odd one is a type name
        deg = len(h_attrs)  # The degree of the relation is the number of attributes (columns)

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
        print(f"\n-- Relation: {relation} --")
        print(tabulate(b_rows, h_attrs, tablefmt="outline"))  # That last parameter chooses our table style
