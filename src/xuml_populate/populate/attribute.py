"""
attribute.py – Process parsed attribute to populate the metamodel db
"""

# System
import logging
from typing import Set, Optional

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.exceptions.action_exceptions import UndefinedAttribute
from xuml_populate.populate.mm_type import MMtype
from xuml_populate.populate.mmclass_nt import (
    Attribute_i, Non_Derived_Attribute_i, Model_Attribute_i,
    Identifier_i, Irreducible_Identifier_i, Super_Identifier_i, Identifier_Attribute_i,
    Default_Initial_Value_i
)

UNRESOLVED = '__unresolved__'  # Attribute type is referential and type resolution is deferred

_logger = logging.getLogger(__name__)


class Attribute:
    """
    Populate all relevant Attribute relvars
    """

    record = None
    dtype = None
    participating_ids = None

    @classmethod
    def defined(cls, name: str, class_name: str, domain: str) -> bool:
        """
        Is this attribute defined?

        Returns:
            True if the attribute is defined
        """
        R = f"Name:<{name}>, Class:<{class_name}>, Domain:<{domain}>"
        attribute_r = Relation.restrict(db=mmdb, relation="Attribute", restriction=R)
        return bool(attribute_r.body)

    @classmethod
    def scalar(cls, name: str, tname: str, domain: str) -> str:
        """
        Returns the name of the Scalar (Type) of the specified Attribute.

        Raises an exception if the Attribute is not defined on the specified Class.

        Args:
            name: Attribute name
            tname: Table (possibly Class) name
            domain: Domain name

        Returns:

            Name of Attribute's Scalar (Type)
        """
        R = f"Name:<{name}>, Non_scalar_type:<{tname}>, Domain:<{domain}>"
        model_attr_r = Relation.restrict(db=mmdb, relation='Model Attribute', restriction=R, svar_name="model_attr_rv")
        if not model_attr_r.body:
            _logger.error(f"Undefined attribute: [{name}:{tname}:{domain}]")
            raise UndefinedAttribute
        class_attr_r = Relation.semijoin(db=mmdb, rname1="model_attr_rv", rname2="Attribute",
                                         attrs={"Name":"Name", "Non_scalar_type":"Class", "Domain":"Domain"})
        if class_attr_r.body:
            return class_attr_r.body[0]['Scalar']

        table_attr_r = Relation.semijoin(db=mmdb, rname1="model_attr_rv", rname2="Table_Attribute",
                                         attrs={"Name":"Name", "Non_scalar_type":"Table", "Domain":"Domain"})
        if table_attr_r.body:
            return table_attr_r.body[0]['Scalar']

    @classmethod
    def populate(cls, tr: str, domain: str, cname: str, class_identifiers: Set[int], record):
        """
        Populate all relevant Attribute relvars

        :param tr: The open db transaction name
        :param domain: The domain name
        :param cname: The class name
        :param class_identifiers: The set of class identifier numbers
        :param record: The parsed class information
        """

        cls.record = record
        cls.dtype = record.get('type', UNRESOLVED)
        participating_ids = cls.record.get('I', [])  # This attr might not participate in any identifier
        # Populate the Attribute's type if it hasn't already been populated
        MMtype.populate_unknown(name=cls.dtype, domain=domain)
        Relvar.insert(db=mmdb, tr=tr, relvar='Attribute', tuples=[
            Attribute_i(Name=record['name'], Class=cname, Domain=domain, Scalar=cls.dtype)
        ])
        Relvar.insert(db=mmdb, tr=tr, relvar='Model_Attribute', tuples=[
            Model_Attribute_i(Name=record['name'], Domain=domain, Non_scalar_type=cname)
        ])
        derived = record.get('derived')
        if not derived:
            Relvar.insert(db=mmdb, tr=tr, relvar='Non_Derived_Attribute', tuples=[
                Non_Derived_Attribute_i(Name=record['name'], Class=cname, Domain=domain)
            ])
            default_value = record.get('default_value')
            if default_value:
                Relvar.insert(db=mmdb, tr=tr, relvar='Default Initial Value', tuples=[
                    Default_Initial_Value_i(Attribute=record['name'], Class=cname, Domain=domain, Value=default_value)
                ])

        else:
            # TODO: Handle derived attribute population later
            pass

        for i in participating_ids:
            # Add Identifier if it is not already in the population
            if i.number not in class_identifiers:
                Relvar.insert(db=mmdb, tr=tr, relvar='Identifier', tuples=[
                    Identifier_i(Number=i.number, Class=cname, Domain=domain)
                ])
                if not i.superid:
                    Relvar.insert(db=mmdb, tr=tr, relvar='Irreducible_Identifier', tuples=[
                        Irreducible_Identifier_i(Number=i.number, Class=cname, Domain=domain)
                    ])
                else:
                    Relvar.insert(db=mmdb, tr=tr, relvar='Super_Identifier', tuples=[
                        Super_Identifier_i(Number=i.number, Class=cname, Domain=domain)
                    ])
                class_identifiers.add(i.number)

            # Include this attribute in this identifier
            Relvar.insert(db=mmdb, tr=tr, relvar='Identifier_Attribute', tuples=[
                Identifier_Attribute_i(Identifier=i.number, Attribute=record['name'], Class=cname, Domain=domain)
            ])

    @classmethod
    def ResolveAttrTypes(cls, domain: str):
        """
        Determine an update type of each unresolved (referential) attribute
        """
        # TODO: Make this first part work and deprecate second
        R = f"Scalar:<{UNRESOLVED}>, Domain:<{domain}>"
        Relation.restrict(db=mmdb, relation='Attribute', restriction=R)
        uattrs = Relation.project(db=mmdb, attributes=('Name', 'Class'))

        # Rather than batch all the updates, we do them one by one
        # This reduces the search space for each subsequent type resolution
        for a in uattrs.body:
            assign_type = cls.ResolveAttr(attr=a['Name'], cname=a['Class'], domain=domain)
            Relvar.updateone(db=mmdb, relvar_name='Attribute',
                             id={'Name': a['Name'], 'Class': a['Class'], 'Domain': domain},
                             update={'Scalar': assign_type})

        # All attr types resolved, so delete the dummy UNRESOLVED type
        MMtype.depopulate_scalar(name=UNRESOLVED, domain=domain)

    @classmethod
    def ResolveAttr(cls, attr: str, cname: str, domain: str) -> str:
        """
        The modeler specifies explicit types only for non-referential attributes.
        This means that all attributes with unresolved types are referential.

        We need to obtain one (there could be multiple) Attribute Reference where the unresolved attribute is a source
        *From attribute* referring to some *To attribute*. Then we check the type of that *To attribute*.

        If the type is not <unresolved>, we return it. Otherwise, we recursively apply the same process to
        the *To attribute*.

        The chain of references must eventually land on a specified type if the model has been properly formalized.

        :param attr: Unresolved attribute: A referential attribute with an unresolved type
        :param cname: The class name
        :param domain: The domain name
        :return: Type name to assign
        """
        _logger.info(f"Resolving attribute type [{cname}.{attr}]")
        # We join the two relvars on the To_attribute so that we can obtain that attribute's Type

        Relation.join(db=mmdb, rname1='Attribute', rname2='Attribute_Reference',
                      attrs={'Name': 'To_attribute', 'Class': 'To_class', 'Domain': 'Domain'})

        # Finally, we restrict and project on our from attribute to get its reference type
        R = f"From_attribute:<{attr}>, From_class:<{cname}>, Domain:<{domain}>"
        from_attrs = Relation.restrict(db=mmdb, restriction=R)

        # The same attribute could participate in multiple References, so we just pick one arbitrarily
        aref = from_attrs.body[0]
        to_name, to_class, to_type = aref['Name'], aref['Class'], aref['Scalar']

        if to_type != UNRESOLVED:
            return to_type  # The To_attribute has a type
        else:
            # The To_attribute is also unresolved. Resolve it!
            return cls.ResolveAttr(attr=to_name, cname=to_class, domain=domain)
