"""
relvar.py – TclRAL operations on relvars
"""

import logging
from typing import List, Dict, Any
from PyRAL.rtypes import Attribute, Mult, delim
from PyRAL.transaction import Transaction
from PyRAL.command import Command
from collections import namedtuple
from tkinter import Tk

class Relvar:
    """
    A relational variable (table)

    TclRAL does not support spaces in names, but PyRAL accepts space delimited names.
    But each space delimiter will be replaced with an underscore delimiter before submitting to TclRAL
    """
    _logger = logging.getLogger(__name__)

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

        :param tclral: The tclRAL session
        :param name: Name of the association, an association Rnum in SM xUML
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
        Command.execute(tclral, cmd=cmd, log=False)
        # Verify and log the constraint by executing the TclRAL constraint command
        verify_cmd = f"relvar constraint info {name}"
        Command.execute(tclral, cmd=verify_cmd)

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

        :param tclral: The TclRAL session
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
        Command.execute(tclral, cmd=cmd, log=False)
        # Verify and log the constraint by executing the TclRAL constraint command
        verify_cmd = f"relvar constraint info {name}"
        Command.execute(tclral, cmd=verify_cmd)

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

        :param relvar: The name of an existing relvar
        :param tuples: A list of tuples named such that the attributes exactly match the relvar header
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
    def create_partition(cls, tclral: Tk, name: str,
                         superclass_name: str, super_attrs: List[str], subs: Dict[str, List[str]]):
        """
        A partition is defined such that the set of tuples in a super relvar is referenced by
        the tuples distributed across a set of one or more sub relvars. Each tuple in a sub
        relvar references some tuple in the super relvar and each tuple in the super relvar is
        referenced by one tuple in one of its sub relvars.

        This constraint implies that the tuples in the super relvar are completely partitioned
        into the disjoint sub sets given by the complete set of sub relvars.

        This constraint is used in SM xUML to support generalization relationships where
        a superclass instance population is paritioned across two or more subclass instance
        populations.

        The TclRAL syntax is:
            relvar partition <name> <super> <superAttrList>
                <sub1> <sub1AttrList>
                ...

        A TclRAL command example is:
            relvar partition R14 Subsystem_Element {Label Domain} Relationship {Rnum Domain} Class {Cnum Domain}

        This is generated from the PyRAL input:
            name: 'R14'
            superclass_name: 'Subsystem Element'
            super_attrs: ['Label', 'Domain']
            subs: {'Relationship': ['Rnum', 'Domain'], 'Class':['Cnum', 'Domain']}

        In the above examples both Relationship.Rnum and Class.Cnum refer to the Subsystem Element.Label
        attribute. So the ordering of identifier attributes for each relvar is significant.

        :param tclral: The tclRAL session
        :param name: Name of the partition, a generalizaiton rnum in SM xUML
        :param superclass_name: Name of the superclass relvar
        :param super_attrs: A list of attributes constituting an identifier of the superclass referenced by
        :param subs:
        """
        super_attrs_str = '{' + ' '.join(super_attrs) + '}'
        all_subs = ""
        for subname, attrs in subs.items():
            all_subs += subname + ' ' + '{' + ' '.join(attrs) + '} '
        all_subs = all_subs[:-1]

        cmd = f"relvar partition {name} {superclass_name} {super_attrs_str} {all_subs}"
        # Execute the command and log the result
        Command.execute(tclral, cmd=cmd, log=False)
        # Verify and log the constraint by executing the TclRAL constraint command
        verify_cmd = f"relvar constraint info {name}"
        Command.execute(tclral, cmd=verify_cmd)

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
        return Command.execute(tclral, cmd)

    @classmethod
    def updateone(cls, tclral: Tk, relvar_name: str, id:Dict, update:Dict[str,Any]):
        """
        Modifies in place at most one tuple of the relvar's value.

        TclRAL syntax:
            relvar updateone <relvarName> <tupleVarName> <id-name-value-list> <script>

        Here is an example where an instance of Attribute in the SM Metamodel has its Type attribute updated:
        The TclRAL command (all on one line, but idented for readability here) is:
            relvar updateone Attribute t
                {Name {Floor} Class {Accessible Shaft Level} Domain {Elevator Management} }
                {tuple update $t Type {Level Name}}

        Generated from the PyRAL:
            relvar_name: 'Attribute'
            id: {'Name': 'Floor', 'Class': 'Accessible Shaft Level', 'Domain': 'Elevator Management'}
            update: {'Type': 'Level Name'}

        :param tclral: The tclRAL session
        :param relvar_name: The relvar to be updated
        :param id: Identifier value for the tuple to be updated
        :param update: A dictionary of attribute value pairs whose values will be applied
        :return: A relation value with the same heading as the value held in relvarName and whose body contains either
        the single tuple that was updated or is empty if no matching tuple was found.
        """
        id_str = ""
        for id_attr,id_val in id.items():
            id_str += f"{id_attr} {{{id_val}}} "
        update_str = ""
        for u_attr,u_val in update.items():
            update_str += u_attr + " {" + u_val + "}"
        cmd = f'relvar updateone {relvar_name} t {{{id_str}}} {{tuple update $t {update_str}}}'
        return Command.execute(tclral, cmd)