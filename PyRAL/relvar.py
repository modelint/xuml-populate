"""
relvar.py – TclRAL operations on relvars
"""

import logging
from tabulate import tabulate
import re
from typing import List, Dict, Any
from PyRAL.rtypes import Attribute, Mult, delim
from PyRAL.transaction import Transaction
from collections import namedtuple
from tkinter import Tk, TclError

class Relvar:
    """
    A relational variable (table)

    TclRAL does not support spaces in names, but PyRAL accepts space delimited names.
    But each space delimiter will be replaced with an underscore delimiter before submitting to TclRAL
    """
    _logger = logging.getLogger(__name__)

    @classmethod
    def command(cls, tclral: Tk, cmd: str, log: bool=True) -> str:
        """
        Executes a TclRAL command via the supplied session and returns TclRAL's string result.

        :param tclral: The TclRAL session
        :param cmd: A TclRAL command string
        :param log:  If false, the result will not be logged. Useful when no meaningful result is expected
        :return: The string received as a result of executing the command
        """
        cls._logger.info(f"cmd: {cmd}")
        try:
            result = tclral.eval(cmd)
        except TclError as e:
            cls._logger.exception(e)
            raise

        if log:
            cls._logger.info(f"result: {result}")
        return result

    # TclRAL commands organized in alphabetic order to match the TclRAL man pages

    @classmethod
    def create_association(cls, tclral: Tk, name: str,
                           from_relvar: str, from_attrs: List[str], from_mult: Mult,
                           to_relvar: str, to_attrs: List[str], to_mult: Mult,
                           ):
        """
        Create a named referential association between two relvars. TclRAL returns an empty string and PyRAL
        does not return any value.

        An association declares that a source relvar has attributes that refer to an identifier of a target relvar.
        In this method we'll use the terms "from" and "to" to describe the corresponding association elements.

        The referring and referred to attribute lists are ordered and "from" attributes refer to the corresponding
        "to" attributes.

        The set of "to" attributes must constitute an identifier for the "to" relvar.

        Multiplicity and conditionality are specified as M, 1, Mc or 1c with the meanings:

            M - at least one
            1 - exactly one
            Mc - zero or more
            1c - zero or one

        :param tclral:
        :param name:
        :param from_relvar: The referring relvar (source)
        :param from_attrs: The referential attributes in the source relvar
        :param from_mult: Multiplicity conditionality associated with the source side of the association
        :param to_relvar: The referenced relvar (target)
        :param to_attrs: The referential attributes in the target relvar
        :param to_mult: Multiplicity conditionality associated with the target side of the association
        """
        # Join each attribute list into a string
        from_attr_str = "{" + ' '.join(from_attrs) + '}'
        to_attr_str = "{" + ' '.join(to_attrs) + '}'

        # Build a TclRAL command string
        cmd = f"relvar association {name} {from_relvar} {from_attr_str} {from_mult.value}" \
              f" {to_relvar} {to_attr_str} {to_mult.value}"

        # Execute the command and ignore the result
        cls.command(tclral, cmd=cmd, log=False)
        # Verify and log the constraint by executing the TclRAL constraint command
        verify_cmd = f"relvar constraint info {name}"
        cls.command(tclral, cmd=verify_cmd)

    @classmethod
    def create_correlation(cls, tclral: Tk, name: str, correlation_relvar: str,
                           correl_a_attrs: List[str], a_mult: Mult, a_relvar: str, a_ref_attrs: List[str],
                           correl_b_attrs: List[str], b_mult: Mult, b_relvar: str, b_ref_attrs: List[str],
                           complete: bool = False):
        """
        A relvar can manage a correlation between tuples in one or two other relvars.

        An association class in Shlaer-Mellor xUML is represented by such a relvar correlation.

        The referential correlation is between a correlation relvar and two other relvars A and B.

        Correlations declare that every tuple in the correlation relvar refers to exactly one tuple of
        relvar A and exactly one tuple of relvar B. (we use lower case a and b here in the code)

        The correlation A attributes refer to an identifier of relvar A and similarly for the B components.

        Multiplicity and conditionality is specified the same as in the create_association command.

        Syntax from the TclRAL man page:
        relvar correlation ?-complete? name correlRelvar
             correlAttrListA refToSpecA refToRelvarA refToAttrListA
             correlAttrListB refToSpecB refToRelvarB refToAttrListB

        Example TclRAL command from the TclRAL man page
        PyRAL:

            relvar correlation C1 OWNERSHIP
                OwnerName + OWNER OwnerName
                DogName * DOG DogName

        Additional example from the SM metamodel
            (See SM class-attribute subsystem with participating classesIdentifier and Attribute where
            the R22 association is:
                Identifier requires M Attribute / Attribute is required in Mc Identifier
                using association class Identifier Attribute):

            PyRAL input:
                name: R22, correlation_relvar: Identifier_Attribute
                corel_a_attrs: ['Identifier', 'Class', 'Domain']
                a_mult: Mc
                a_ref_attrs: ['Number', 'Class', 'Domain']
                corel_b_attrs: ['Attribute', 'Class', 'Domain']
                b_mult: M
                b_ref_attrs: ['Name', 'Class', 'Domain']

            TclRAL generated command
                relvar correlation R22 Identifier_Attribute
                    {Identifier Class Domain} + Identifier
                    {Number Class Domain} {Attribute Class Domain} * Attribute {Name Class Domain}

        :param tclral:  The TclRAL session
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
        # relvar tuples. The latter approach matches the way Shlaer-Mellor xUML modelers think.
        cmd = f"relvar correlation {'-complete ' if complete else ''}{name} {correlation_relvar} " \
              f"{correl_a_attrs_str} {b_mult.value} {a_relvar} {a_ref_attrs_str} " \
              f"{correl_b_attrs_str} {a_mult.value} {b_relvar} {b_ref_attrs_str}"

        # Execute the command and log the result
        cls.command(tclral, cmd=cmd, log=False)
        # Verify and log the constraint by executing the TclRAL constraint command
        verify_cmd = f"relvar constraint info {name}"
        cls.command(tclral, cmd=verify_cmd)

    @classmethod
    def insert(cls, relvar: str, tuples: List[namedtuple]):
        """
        Specifies the insert of a set of tuples into the value of the relvar, modifying it in place.

        Rather than execute the insert operation immediately, it is added as a statement to the currently
        open transaction. The Transaction append operation will raise an exception if no
        transaction is currently open.

        It is often the case that a set of inserts must be executed together as a transaction
        so that relvar constraints may be checked. For example, an SM xUML super and subclass insert must
        be applied as a single transaction. In cases where a single, standalone insert will suffice,
        it is simply wrapped as a single statement transaction for simplicity.

        TclRAL does not require that a single insert be embedded in an explicit transaction so,
        in the future, a standalone insert may be supported by PyRAL.

        The TclRAL syntax is:
            relvar insert <relvarName> ?<name-value-list> ...?

        TclRAL example where an instance of Class is inserted into the SM xUML metamodel:
            relvar insert Class {Name {Accessible Shaft Level} Cnum {C1} Domain {Elevator Management}}

        Where PyRAL input is:
            relvar: 'Class'
            tuples: [ Class_i(Name='Accessible Shaft Level', Cnum='C1', Domain='Elevator Management') ]


        Note that the emtpy set may be provided which results in a no-op.
        PyRAL supports this feature by allowing an empty list of tuples to be specified

        :relvar: The name of an existing relvar
        :tuples: A list of tuples named such that the attributes exactly match the relvar header
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


    @classmethod
    def create_relvar(cls, tclral: Tk, name: str, attrs: List[Attribute], ids: Dict[int, List[str]]) -> str:
        """
        Create a relvar

        Syntax from the TclRAL man page:
            relvar create <relvarName> <heading> <id1> ?id2 ...?

        Example TclRAL command:
            relvar create Waypoint {WPT_number int, Lat string, Long string, Frequency double} {WPT_number} {Lat Long}

        This class has both a single attribute identifier "WPT_number" and a multiple attribute identifier {Lat Long}
        We wrap each identifier in {} brackets for simplicity even though we only really need them to group
        multiple attribute identifiers

        :param tclral: A TclRAL session
        :param name: Name of the new relvar
        :param attrs: A list of Attributes (name, type - named tuples)
        :param ids: A dictionary of {idnum: [attr_name, ...] } values
        :return: The relation defined by the empty relvar in the form: <heading> {}
        """
        # A header is a bracketed list of attribute name pairs such as:
        #   {WPT_number int, Lat string, Long string, Frequency double}
        header = "{"
        for a in attrs:
            # We need to replace any spaces in an attribute name with underscores
            header += f"{a.name.replace(' ', delim)} {a.type.replace(' ', delim)} "
        header = header[:-1] + "}" # Replace the trailing space with a closing bracket

        # Now we make the list of identifiers such as:
        #   {WPT_number} {Lat Long}
        id_list = ""
        for inum, attrs in ids.items():
            # Create a bracketed list for each identifier
            id_list += '{'
            for a in attrs:
                id_list += f"{a.replace(' ', delim)} "
            id_list = id_list[:-1] + '} '
        id_list = id_list[:-1]

        # Build and execute the TclRAL command
        cmd = f"relvar create {name} {header} {id_list}"
        return cls.command(tclral, cmd)

    @classmethod
    def create_partition(cls, db: Tk, name: str,
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
    def updateone(cls, db: Tk, relvar_name: str, id:Dict, update:Dict[str,Any]):
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
    def population(cls, db: Tk, relvar: str):
        """

        :param db:
        :param relvar:
        :return:
        """
        result = db.eval(f"set {relvar}")
        # tclral.eval(f"puts ${relvar}")

    @classmethod
    def relformat(cls, db: Tk, relvar: str):
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