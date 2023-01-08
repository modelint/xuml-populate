"""
attribute.py – Create an attribute relation
"""

import logging
from PyRAL.relvar import Relvar
from PyRAL.relation import Relation
from typing import Set
from class_model_dsl.populate.pop_types import \
    Attribute_i, Non_Derived_Attribute_i,\
    Identifier_i, Irreducible_Identifier_i, Super_Identifier_i, Identifier_Attribute_i
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tkinter import Tk


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
        cls.dtype = record.get('type', "<unresolved>")
        participating_ids = cls.record.get('I', [])  # This attr might not participate in any identifier
        Relvar.insert(db=mmdb, relvar='Attribute', tuples=[
            Attribute_i(Name=record['name'], Class=cname, Domain=domain, Type=cls.dtype)
        ])
        # TODO: Check for derived or non-derived, for now assume the latter
        Relvar.insert(db=mmdb, relvar='Non_Derived_Attribute', tuples=[
            Non_Derived_Attribute_i(Name=record['name'], Class=cname, Domain=domain)
        ])

        for i in participating_ids:
            # Add Identifier if it is not already in the population
            if i.number not in class_identifiers:
                Relvar.insert(db=mmdb, relvar='Identifier', tuples=[
                    Identifier_i(Number=i.number, Class=cname, Domain=domain)
                ])
                if not i.superid:
                    Relvar.insert(db=mmdb, relvar='Irreducible_Identifier', tuples=[
                        Irreducible_Identifier_i(Number=i.number, Class=cname, Domain=domain)
                    ])
                else:
                    Relvar.insert(db=mmdb, relvar='Super_Identifier', tuples=[
                        Super_Identifier_i(Number=i.number, Class=cname, Domain=domain)
                    ])
                class_identifiers.add(i.number)

            # Include this attribute in this identifier
            Relvar.insert(db=mmdb, relvar='Identifier_Attribute', tuples=[
                Identifier_Attribute_i(Identifier=i.number, Attribute=record['name'], Class=cname, Domain=domain)
            ])

            # TODO convert below from SQL to TclRAL (after ref subsystem added)


    @classmethod
    def ResolveAttrTypes(cls, mmdb: 'Tk', domain: str):
        """
        Determine an update type of each unresolved (referential) attribute
        """

        # Get the set of all attributes with unresolved types
        Relation.restrict(db=mmdb, relation='Attribute',
                                   restriction=f'Type:<unresolved>, Domain:{domain}')
        result = Relation.project(db=mmdb, attributes=['Name', 'Class'])
        uattrs = Relation.make_pyrel(relation=result)
        Relation.relformat2(uattrs)

        # Rather than batch all the updates, we do them one by one
        # This reduces the search space for each subsequent type resolution
        for a in uattrs.body:
            assign_type = cls.ResolveAttr(
                attr_name=a['Name'], class_name=a['Class'], domain_name=domain
            )
            # Update the attribute instance with the assigned type
        pass



    @classmethod
    def ResolveAttr(cls, attr_name: str, class_name: str, domain_name: str) -> str:
        """
        The modeler specifies explicit types only for non-referential attributes. This means that all attributes with
        unresolved types are referential.

        We need to obtain one (there could be multiple) Attribute Reference where the unresolved attribute is a source
        *From attribute* referring to some *To attribute*. Then we check the type of that *To attribute*. If the type is
        not <unresolved>, we return it. Otherwise, we recursively apply the same process to the *To attribute*. The chain
        of references must eventually land on a specified type if the model has been properly formalized.

        :param attr: Unresolved attribute: A referential attribute with an unresolved type
        :return:  Type name to assign
        """
        cls._logger.info(f"Resolving attribute type [{attr}]")
    #     # Select one attribute reference where the attribute is the source
    #     aref_t = smdb.MetaData.tables['Attribute Reference']
    #     attr_t = smdb.MetaData.tables['Attribute']
    #     # We join the two relvars on the To_attribute so that we can obtain that attribute's Type
    #     # j = join, r = restrict, p = project, q = query, and row is the query result
    #     j = join(aref_t, attr_t,
    #              and_(
    #                  (aref_t.c['To attribute'] == attr_t.c.Name),
    #                  (aref_t.c['To class'] == attr_t.c.Class),
    #                  (aref_t.c.Domain == attr_t.c.Domain),
    #              ),
    #              )
    #     r = and_(
    #         (aref_t.c['From attribute'] == attr.name),
    #         (aref_t.c['From class'] == attr.mmclass),
    #         (aref_t.c.Domain == attr.domain),
    #     )
    #     p = [aref_t.c['To attribute'], aref_t.c['To class'], attr_t.c.Type]  # Project the target attribute and its type
    #     q = select(p).select_from(j).where(r)
    #     row = smdb.Connection.execute(q).fetchone()  # There could be many, but we only need one
    #     refattr = I_Attribute(name=row['To attribute'], mmclass=row['To class'], domain=attr.domain)
    #     if row['Type'] != '<unresolved>':
    #         return row['Type']  # The To_attribute has a type
    #     else:
    #         return ResolveAttr(attr=refattr)  # The To_attribute is also unresolved. Resolve it!


