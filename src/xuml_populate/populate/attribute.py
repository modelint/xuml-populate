"""
attribute.py – Process parsed attribute to populate the metamodel db
"""

import logging
from xuml_populate.config import mmdb
from typing import Set
from pyral.relvar import Relvar
from pyral.relation import Relation
from xuml_populate.exceptions.action_exceptions import UndefinedAttribute
from xuml_populate.populate.mm_type import MMtype
from xuml_populate.populate.mmclass_nt import \
    Attribute_i, Non_Derived_Attribute_i, Model_Attribute_i, \
    Identifier_i, Irreducible_Identifier_i, Super_Identifier_i, Identifier_Attribute_i

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
    def scalar(cls, name: str, cname: str, domain: str) -> str:
        """
        Returns the name of the Scalar (Type) of the specified Attribute.

        Raises an exception if the Attribute is not defined on the specified Class.

        :param name:  Attribute name
        :param cname:  Class name
        :param domain:  Domain name
        :return: Name of Attribute's Scalar (Type)
        """
        R = f"Name:<{name}>, Class:<{cname}>, Domain:<{domain}>"
        result = Relation.restrict(mmdb, relation='Attribute', restriction=R)
        if not result.body:
            _logger.error(f"Undefined attribute: [{name}:{cname}:{domain}]")
            raise UndefinedAttribute
        return result.body[0]['Scalar']

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
        Relvar.insert(mmdb, tr=tr, relvar='Attribute', tuples=[
            Attribute_i(Name=record['name'], Class=cname, Domain=domain, Scalar=cls.dtype)
        ])
        Relvar.insert(mmdb, tr=tr, relvar='Model_Attribute', tuples=[
            Model_Attribute_i(Name=record['name'], Domain=domain, Non_scalar_type=cname)
        ])
        # TODO: Check for derived or non-derived, for now assume the latter
        Relvar.insert(mmdb, tr=tr, relvar='Non_Derived_Attribute', tuples=[
            Non_Derived_Attribute_i(Name=record['name'], Class=cname, Domain=domain)
        ])

        for i in participating_ids:
            # Add Identifier if it is not already in the population
            if i.number not in class_identifiers:
                Relvar.insert(mmdb, tr=tr, relvar='Identifier', tuples=[
                    Identifier_i(Number=i.number, Class=cname, Domain=domain)
                ])
                if not i.superid:
                    Relvar.insert(mmdb, tr=tr, relvar='Irreducible_Identifier', tuples=[
                        Irreducible_Identifier_i(Number=i.number, Class=cname, Domain=domain)
                    ])
                else:
                    Relvar.insert(mmdb, tr=tr, relvar='Super_Identifier', tuples=[
                        Super_Identifier_i(Number=i.number, Class=cname, Domain=domain)
                    ])
                class_identifiers.add(i.number)

            # Include this attribute in this identifier
            Relvar.insert(mmdb, tr=tr, relvar='Identifier_Attribute', tuples=[
                Identifier_Attribute_i(Identifier=i.number, Attribute=record['name'], Class=cname, Domain=domain)
            ])

    @classmethod
    def ResolveAttrTypes(cls, domain: str):
        """
        Determine an update type of each unresolved (referential) attribute
        """
        # TODO: Make this first part work and deprecate second
        R = f"Scalar:<{UNRESOLVED}>, Domain:<{domain}>"
        Relation.restrict(mmdb, relation='Attribute', restriction=R)
        uattrs = Relation.project(mmdb, attributes=('Name', 'Class'))

        # Rather than batch all the updates, we do them one by one
        # This reduces the search space for each subsequent type resolution
        for a in uattrs.body:
            assign_type = cls.ResolveAttr(attr=a['Name'], cname=a['Class'], domain=domain)
            Relvar.updateone(mmdb, relvar_name='Attribute',
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

        Relation.join(mmdb, rname1='Attribute', rname2='Attribute_Reference',
                      attrs={'Name': 'To_attribute', 'Class': 'To_class', 'Domain': 'Domain'})

        # Finally, we restrict and project on our from attribute to get its reference type
        R = f"From_attribute:<{attr}>, From_class:<{cname}>, Domain:<{domain}>"
        from_attrs = Relation.restrict(mmdb, restriction=R)

        # The same attribute could participate in multiple References, so we just pick one arbitrarily
        aref = from_attrs.body[0]
        to_name, to_class, to_type = aref['Name'], aref['Class'], aref['Scalar']

        if to_type != UNRESOLVED:
            return to_type  # The To_attribute has a type
        else:
            # The To_attribute is also unresolved. Resolve it!
            return cls.ResolveAttr(attr=to_name, cname=to_class, domain=domain)
