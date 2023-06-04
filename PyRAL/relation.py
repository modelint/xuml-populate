"""
relation.py – Operations on relations
"""

import logging
import re
from tabulate import tabulate
from typing import List, Optional, Dict
from PyRAL.rtypes import RelationValue
from PyRAL.command import Command

from tkinter import Tk

# If we want to apply successive (nested) operations in TclRAL we need to have the result
# of each TclRAL command saved in tcl variable. So each time we execute a command that produces
# a relation result we save it. The variable name is chosen so that it shouldn't conflict with
# any user relvars. Do not ever use the name below as one of your user relvars!
# For any given command, if no relvar is specified, the previous relation result is assumed
# to be the input.
_relation = r'^relation'  # Name of the latest relation result. Carat prevents name collision
session_variable_names = set() # Maintain a list of temporary variable names in use


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

           attr1:str1; attr2:str2, ...

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
        match_strings = selection.split(';')
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
    def set_var(cls, tclral: Tk, name: str):
        """
        Set a temporary TclRAL relation variable to the most recent returned result.
        This allows us to save a particular TclRAL return value string so that we can plug it
        into a subsequent TclRAL operation.

        :param tclral: The TclRAL session
        :param name: The variable name (must be a legal Tcl variable name
        """
        session_variable_names.add(name)
        tclral.eval(f"set {name} ${{{_relation}}}")

    @classmethod
    def make_attr_list(cls, attrs: Dict[str, str]) -> str:
        """
        Makes a TclRAL attrList to be inserted in a command
        :param attrs:
        :return:
        """
        attr_list = "{"
        for k,v in attrs.items():
            attr_list += f"{k} {v} "
        return attr_list[:-1] + "}"

    @classmethod
    def join(cls, tclral: Tk, rname2: str, rname1: str=_relation, attrs: Dict[str, str]={},
             svar_name: Optional[str]=None) -> str:
        """
        Perform a natural join on two relations using an optional attribute mapping. If no attributes are specified,
        the join is performed on same named attributes.

        :param tclral: The TclRAL session
        :param rname1: Name of one relvar to join
        :param rname2: Name of the other relvar
        :param attrs: Dictionary in format { r1.attr_name: r2.attr_name, ... }
        :param svar_name: Relation result is stored in this optional TclRAL variable for subsequent operations to use
        :return Resulting relation as a TclRAL string
        """
        cmd = f'set {{{_relation}}} [relation join ${{{rname1}}} ${rname2}'
        if attrs:
            cmd += " -using " + cls.make_attr_list(attrs)
        cmd += ']'
        result = Command.execute(tclral, cmd)
        if svar_name:  # Save the result using the supplied session variable name
            cls.set_var(tclral, svar_name)
        return result

    @classmethod
    def project(cls, tclral: Tk, attributes: List[str], relation: str=_relation, svar_name: Optional[str]=None) -> str:
        """
        Returns a relation whose heading consists of only a set of selected attributes.
        The body of the result consists of the corresponding tuples from the specified relation,
        removing any duplicates created by considering only a subset of the attributes.

        :param tclral: The TclRAL session
        :param attributes: Attributes to be projected
        :param relation: The relation to be projected
        :param svar_name: Relation result is stored in this optional TclRAL variable for subsequent operations to use
        :return Resulting relation as a TclRAL string
        """
        projection = ' '.join(attributes)
        cmd = f'set {_relation} [relation project ${{{relation}}} {projection.strip()}]'
        result = Command.execute(tclral, cmd)
        if svar_name:  # Save the result using the supplied session variable name
            cls.set_var(tclral, svar_name)
        return result

    @classmethod
    def rename(cls, tclral: Tk, names: Dict[str, str], relation: str=_relation, svar_name: Optional[str]=None) -> str:
        """
        (NOTE: I only just NOW realized that the TclRAL join command provides an option to specify multiple renames
        as part of a join, because, of course it does! Argghh. So there may not be any need to perform multiple renames
        at once, but hey, there's no harm in providing potentially superfluous functionality as it does at least
        handle the single rename case. - LS)

        Given an input relation, rename one or more attributes from old to new names. This is useful when you want
        to join two relvars on attributes with differing names.

        In SM xUML, it is common for an attribute with one name to reference another attribute of the same
        type but a different name, Employee_ID -> Manager, for exmaple.

        We often need to rename multiple attributes before performing a join, so the single attribute rename
        operation provided by TclRAL is executed once for each element of the names dictionary.

        TclRAL rename syntax:
            relation rename <relationValue> ?oldname newname ...?

        Multiple rename example in TclRAL:
            relation rename ${Attribute_Reference} To_attribute Name
            relation rename ${^relation} To_class Class

        (^relation) is the name of PyRAL's intermediate result session variable, so we are feeding
        the result of the first rename into the next.

        Generated from the PyRAL input:
            relation: 'Attribute_Reference'
            names: {'To_attribute': 'Name', 'To_class': 'Class'}

        :param tclral: The TclRAL session
        :param relation: The relation to rename
        :param names: Dictionary in format { old_name: new_name }
        :param svar_name:  Name of a TclRAL session variable named for future reference
        :return Resulting relation as a TclRAL string
        """
        r = relation
        result = None
        # Each attribute rename is executed with a separate command
        for old_name,new_name in names.items():
            # The first rename operation is on the supplied relation
            cmd = f'set {_relation} [relation rename ${{{r}}} {old_name} {new_name}]'
            result = Command.execute(tclral, cmd)
            r = _relation # Subsequent renames are based on the previous result
        if svar_name:  # Save the final result using the supplied session variable name
            cls.set_var(tclral, svar_name)
        return result # Result of the final rename (all renames in place)

    @classmethod
    def restrict(cls, tclral: Tk, restriction: str, relation: str=_relation, svar_name: Optional[str]=None) -> str:
        """
        Here we select zero or more tuples that match the supplied criteria.

        In relational theory this is known as a restriction operation.

        TclRAL syntax:
            relation restrict <relationValue> <tupleVariable> <expression>

        TclRAL command example:
            relation restrict ${Attribute} t {[string match {<unresolved>} [tuple extract $t Type]] &&
                [string match {Elevator Management} [tuple extract $t Domain]]}

        Generated from this PyRAL input:
            relation: Attribute
            restriction: 'Type:<unresolved>, Domain:Elevator Management'


        :param tclral: The TclRAL session
        :param relation: Name of a relation variable where the operation is applied
        :param restriction: A string in Scrall notation that specifies the restriction criteria
        :param svar_name: An optional session variable that holds the result
        :return: The TclRAL string result representing the restricted tuple set
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
        # result = tclral.eval("relation restrict $Attribute a {[string match <unresolved> [tuple extract $a Type]]}")
        cmd = f"set {_relation} [relation restrict ${{{relation}}} t {rexpr}]"
        result = Command.execute(tclral, cmd)
        if svar_name:  # Save the result using the supplied session variable name
            cls.set_var(tclral, svar_name)
        return result

    @classmethod
    def subtract(cls, tclral: Tk, rname2: str, rname1: str=_relation, svar_name: Optional[str]=None) -> str:
        """
        Returns the set difference between two relations using the TclRAL minus command.

        Each relation must be of the same type (same header) as will the result.

        The body of the result consists of those tuples present in r1 but not present in r2.

        Relational subtraction is not commutative so the order of the r1 and r2 arguments is significant.

        The TclRAL syntax is:
            relation minus <relationValue1> <relationValue2>

        TclRAL example taken from the lineage.py Derive method where a set of all classes playing one or more
        subclass roles subtracts all classes playing superclass roles to obtain a set of leaf classes that
        participate as subclasses only.

            relation minus $subs $supers

        Generated from the following PyRAL input:
            rname1: subs
            rname2: supers

        :param tclral: The TclRAL session
        :param rname1: Subtracts value in rname2
        :param rname2: Is subtracted from value in rname1
        :param svar_name: Relation result is stored in this optional TclRAL variable for subsequent operations to use
        :return Subtraction relation as a TclRAL string
        """
        cmd = f'set {_relation} [relation minus ${{{rname1}}} ${rname2}]'
        result = Command.execute(tclral, cmd)
        if svar_name:  # Save the result using the supplied session variable name
            cls.set_var(tclral, svar_name)
        return result

    @classmethod
    def get_rval_string(cls, tclral: Tk, variable_name:str) -> str:
        """
        Obtain a relation from a TclRAL variable

        :param tclral: The TclRAL session
        :param variable_name: Name of a variable containing a relation defined in that session
        :return: TclRAL string representing the relation value
        """
        return Command.execute(tclral, cmd=f"set {variable_name}")

    @classmethod
    def make_pyrel(cls, relation: str, name: str=_relation ) -> RelationValue:
        """
        Take a relation obtained from TclRAL and convert it into a pythonic relation value.
        A RelationValue is a named tuple with a header and a body component.
        The header component will be a dictionary of attribute name keys and type values
        The body component will be a list of relational tuples each defined as a dictionary
        with a key matching some attribute of the header and a value for that attribute.

        :param relation: A TclRAL string representing a relation
        :param name: An optional relvar name
        :return: A RelationValue constructed from the provided relation string
        """
        # First check for the dee/dum edge cases
        if relation.strip() == '{} {}':
            # Tabledum (DUM), no attributes and no tuples (relational false value)
            # Header is an empty dictionary and body is an empty list
            return RelationValue(name=name, header={}, body=[])
        if relation.strip() == '{} {{}}':
            # Tabledum (DEE), no attributes and one empty tuple (relational true value)
            # Header is an empty dictionary and body is a list with one empty dictionary element
            return RelationValue(name=name, header={}, body=[{}])

        # Going forward we can assume that there is at least one attribute and zero or more tuples
        h, b = relation.split('}', 1)  # Split at the first closing bracket to obtain header and body strings

        # Construct the header dictionary
        h_items = h.strip('{').split()  # Remove the open brace and split on spaces (no spaces in TclRAL attr names)
        header = dict(zip(h_items[::2], h_items[1::2]))  # Attribute names for keys and TclRAL types for values

        # Construct the body list
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
        for a in header.keys():
            tuple_pattern += f"{a} {value_pattern} "
        tuple_pattern = tuple_pattern.rstrip(' ')  # Removes the final trailing space
        # Now we can use the constructed tuple pattern regex to extract a list of values
        # from each row to match our attribute list order
        # Here we apply the tuple_pattern regex to each body row stripping the brackets from each value
        # and end up with a list of unbracketed body row values

        # For tabulate we need a list for the columns and a list of lists for the rows

        # Handle case where there are zero body tuples
        at_least_one_tuple = b.strip('{} ')  # Empty string if no tuples in body
        if not at_least_one_tuple:
            return RelationValue(name=name, header=header, body={})

        # There is at least one body tuple
        if len(header) > 1:
            # More than one column and the regex match returns a convenient tuple in the zero element
            # b_rows = [for row in body]
            b_rows = [[f.strip('{}') for f in re.findall(tuple_pattern, row)[0]] for row in body]
        else:
            # If there is only one match (value), regex returns a string rather than a tuple
            # in the zero element. We need to embed this string in a list
            b_rows = [[re.findall(tuple_pattern, row)[0].strip('{}') for row in body]]
        # Either way, b_rows is a list of lists

        body = [dict(zip(header.keys(), r)) for r in b_rows]
        rval = RelationValue(name=name, header=header, body=body)
        return rval

    @classmethod
    def print(cls, tclral: 'Tk', variable_name: str=_relation, table_name:Optional[str]=None):
        """
        Given the name of a TclRAL relation variable, obtain its value and print it as a table.

        :param tclral: The TclRAL session
        :param variable_name: Name of the TclRAL variable to print, also used to name the table if no table_name
        :param table_name:  If supplied, this name is used instead of the variable name to name the printed table
        """
        # convert the TclRAL string value held in the session variable into a PyRAL relation and print it
        rval = cls.make_pyrel(relation=cls.get_rval_string(tclral, variable_name),
                              name=table_name if table_name else variable_name)
        cls.relformat(rval)

    @classmethod
    def relformat(cls, rval: RelationValue):
        """
        Formats the PyRAL relation into a table and prints it using the imported tabulation module

        :param rval: A PyRAL relation value
        """
        # Now we have what we need to generate a table
        # Print the relvar name if supplied, otherwise use the default name for the latest result
        tablename = rval.name if rval.name else '<unnamed>'
        print(f"\n-- {tablename} --")
        attr_names = list(rval.header.keys())
        brows = [list(row.values()) for row in rval.body]
        print(tabulate(tabular_data=brows, headers=attr_names, tablefmt="outline"))  # That last parameter chooses our table style

    @classmethod
    def restrict2(cls, tclral: Tk, restriction: str, relation: str = _relation,
                  svar_name: Optional[str] = None) -> RelationValue:
        """
        Here we select zero or more tuples that match the supplied criteria.

        In relational theory this is known as a restriction operation.

        TclRAL syntax:
            relation restrict <relationValue> <tupleVariable> <expression>

        TclRAL command example:
            relation restrict ${Attribute} t {[string match {<unresolved>} [tuple extract $t Type]] &&
                [string match {Elevator Management} [tuple extract $t Domain]]}

        Generated from this PyRAL input:
            relation: Attribute
            restriction: 'Type:<unresolved>, Domain:Elevator Management'


        :param tclral: The TclRAL session
        :param relation: Name of a relation variable where the operation is applied
        :param restriction: A string in Scrall notation that specifies the restriction criteria
        :param svar_name: An optional session variable that holds the result
        :return: The TclRAL string result representing the restricted tuple set
        """
        # Replace square brackets and logic ops with tcl equivalents
        restrict_tcl = restriction.replace('[', '{').replace(']', '}').\
            replace(' OR ', ' || ').replace(', ', ' && ').replace(' AND ', ' && ').replace('NOT ', '!')
        # Now process ':' attr:value match pairs with tcl string match expressions and wrap with tcl braces
        rexpr = '{' + re.sub(r'([\w_]*):({[\w ]*})', r'[string match \2 [tuple extract $t \1]]', restrict_tcl) + '}'

        # Insert it in the tlcral relation restrict command and execute
        cmd = f"set {_relation} [relation restrict ${{{relation}}} t {rexpr}]"
        result = Command.execute(tclral, cmd)
        if svar_name:  # Save the result using the supplied session variable name
            cls.set_var(tclral, svar_name)
        return cls.make_pyrel(result)

    @classmethod
    def project2(cls, tclral: Tk, attributes: List[str], relation: str=_relation,
                 svar_name: Optional[str]=None) -> RelationValue:
        """
        Returns a relation whose heading consists of only a set of selected attributes.
        The body of the result consists of the corresponding tuples from the specified relation,
        removing any duplicates created by considering only a subset of the attributes.

        :param tclral: The TclRAL session
        :param attributes: Attributes to be projected
        :param relation: The relation to be projected
        :param svar_name: Relation result is stored in this optional TclRAL variable for subsequent operations to use
        :return Resulting relation as a PyRAL relation value
        """
        projection = ' '.join(attributes)
        cmd = f'set {_relation} [relation project ${{{relation}}} {projection.strip()}]'
        result = Command.execute(tclral, cmd)
        if svar_name:  # Save the result using the supplied session variable name
            cls.set_var(tclral, svar_name)
        return cls.make_pyrel(result)

