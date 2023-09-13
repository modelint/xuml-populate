"""
attribute.py – Create an attribute relation
"""

import logging
from pyral.relvar import Relvar
from pyral.relation import Relation
from typing import Set
from xuml_populate.populate.mm_type import MMtype
from xuml_populate.populate.mmclass_nt import \
    Attribute_i, Non_Derived_Attribute_i, Model_Attribute_i,\
    Identifier_i, Irreducible_Identifier_i, Super_Identifier_i, Identifier_Attribute_i
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tkinter import Tk

UNRESOLVED = '__unresolved__' # Attribute type is referential and type resolution is deferred

class Attribute:
    """
    Populate an attribute of a class
    """
    _logger = logging.getLogger(__name__)

    record = None
    dtype = None
    participating_ids = None

    @classmethod
    def populate(cls, mmdb, domain: str, cname: str, class_identifiers: Set[int], record):
        """Constructor"""

        cls.record = record
        cls.dtype = record.get('type', UNRESOLVED)
        participating_ids = cls.record.get('I', [])  # This attr might not participate in any identifier
        # Populate the Attribute's type if it hasn't already been populated
        MMtype.populate_unknown(mmdb, name=cls.dtype, domain=domain)
        Relvar.insert(relvar='Attribute', tuples=[
            Attribute_i(Name=record['name'], Class=cname, Domain=domain, Scalar=cls.dtype)
        ])
        Relvar.insert(relvar='Model_Attribute', tuples=[
            Model_Attribute_i(Name=record['name'], Domain=domain, Non_scalar_type=cname)
        ])
        # TODO: Check for derived or non-derived, for now assume the latter
        Relvar.insert(relvar='Non_Derived_Attribute', tuples=[
            Non_Derived_Attribute_i(Name=record['name'], Class=cname, Domain=domain)
        ])

        for i in participating_ids:
            # Add Identifier if it is not already in the population
            if i.number not in class_identifiers:
                Relvar.insert(relvar='Identifier', tuples=[
                    Identifier_i(Number=i.number, Class=cname, Domain=domain)
                ])
                if not i.superid:
                    Relvar.insert(relvar='Irreducible_Identifier', tuples=[
                        Irreducible_Identifier_i(Number=i.number, Class=cname, Domain=domain)
                    ])
                else:
                    Relvar.insert(relvar='Super_Identifier', tuples=[
                        Super_Identifier_i(Number=i.number, Class=cname, Domain=domain)
                    ])
                class_identifiers.add(i.number)

            # Include this attribute in this identifier
            Relvar.insert(relvar='Identifier_Attribute', tuples=[
                Identifier_Attribute_i(Identifier=i.number, Attribute=record['name'], Class=cname, Domain=domain)
            ])

    @classmethod
    def ResolveAttrTypes(cls, mmdb: 'Tk', domain: str):
        """
        Determine an update type of each unresolved (referential) attribute
        """
        # TODO: Make this first part work and deprecate second
        R = f"Scalar:<{UNRESOLVED}>, Domain:<{domain}>"
        Relation.restrict(tclral=mmdb, relation='Attribute', restriction=R)
        uattrs = Relation.project(tclral=mmdb, attributes=('Name', 'Class'))

        # Rather than batch all the updates, we do them one by one
        # This reduces the search space for each subsequent type resolution
        for a in uattrs.body:
            assign_type = cls.ResolveAttr(mmdb=mmdb,
                attr_name=a['Name'], class_name=a['Class'], domain_name=domain
            )
            Relvar.updateone(tclral=mmdb,
                             relvar_name='Attribute',
                             id={'Name':a['Name'], 'Class':a['Class'], 'Domain':domain},
                             update={'Scalar': assign_type})

        # All attr types resolved, so delete the dummy UNRESOLVED type
        MMtype.depopulate_scalar_type(mmdb, name=UNRESOLVED, domain=domain)

    @classmethod
    def ResolveAttr(cls, mmdb: 'Tk', attr_name: str, class_name: str, domain_name: str) -> str:
        """
        The modeler specifies explicit types only for non-referential attributes. This means that all attributes with
        unresolved types are referential.

        We need to obtain one (there could be multiple) Attribute Reference where the unresolved attribute is a source
        *From attribute* referring to some *To attribute*. Then we check the type of that *To attribute*. If the type is
        not <unresolved>, we return it. Otherwise, we recursively apply the same process to the *To attribute*. The chain
        of references must eventually land on a specified type if the model has been properly formalized.

        :param mmdb: The metamodel tclral session
        :param attr_name: Unresolved attribute: A referential attribute with an unresolved type
        :param class_name:
        :param domain_name:
        :return: Type name to assign
        """
        cls._logger.info(f"Resolving attribute type [{class_name}.{attr_name}]")
        # We join the two relvars on the To_attribute so that we can obtain that attribute's Type

        Relation.join(mmdb, rname1='Attribute', rname2='Attribute_Reference',
                      attrs={'Name':'To_attribute', 'Class':'To_class', 'Domain':'Domain'})

        # Finally, we restrict and project on our from attribute to get its reference type
        R = f"From_attribute:<{attr_name}>, From_class:<{class_name}>, Domain:<{domain_name}>"
        from_attrs = Relation.restrict(mmdb, restriction=R)

        # The same attribute could participate in multiple References, so we just pick one arbitrarily
        aref = from_attrs.body[0]
        to_name, to_class, to_type = aref['Name'], aref['Class'], aref['Scalar']

        if to_type != UNRESOLVED:
            return to_type  # The To_attribute has a type
        else:
            # The To_attribute is also unresolved. Resolve it!
            return cls.ResolveAttr(mmdb=mmdb, attr_name=to_name, class_name=to_class, domain_name=domain_name)