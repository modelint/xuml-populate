"""
attribute.py – Create an attribute relation
"""

import logging
from class_model_dsl.database.sm_meta_db import SMmetaDB as smdb
from sqlalchemy import select, join, and_
from collections import namedtuple

I_Attribute = namedtuple('_I_Attribute', 'name, mmclass, domain')
"""
I_Attribute

Instance reference to Attribute class (See identifier of Attribute class in the metamodel)

- name -- Attribute name
- mmclass -- Class it belongs to (class is a keyword, so we preface with mm (metamodel)
- domain -- Domain of the class
"""


def ResolveAttrTypes():
    """
    Determine an update type of each unresolved (referential) attribute
    """
    attr_t = smdb.MetaData.tables['Attribute']
    p = [attr_t.c.Name, attr_t.c.Class, attr_t.c.Domain]
    q = select(p).where(attr_t.c.Type == "<unresolved>")
    rows = smdb.Connection.execute(q).fetchall()
    uattrs = [I_Attribute(*r) for r in rows]
    # Rather than batch all the updates, we do them one by one
    # This reduces the search space for each subsequent type resolution
    for uattr in uattrs:
        assign_type = ResolveAttr(attr=uattr)
        r = and_(
            (attr_t.c.Name == uattr.name),
            (attr_t.c.Class == uattr.mmclass),
            (attr_t.c.Domain == uattr.domain),
        )
        u = attr_t.update().where(r).values(Type=assign_type)
        smdb.Connection.execute(u)


def ResolveAttr(attr: I_Attribute) -> str:
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
    logging.info(f"Resolving attribute type [{attr}]")
    # Select one attribute reference where the attribute is the source
    aref_t = smdb.MetaData.tables['Attribute Reference']
    attr_t = smdb.MetaData.tables['Attribute']
    # We join the two relvars on the To_attribute so that we can obtain that attribute's Type
    # j = join, r = restrict, p = project, q = query, and row is the query result
    j = join(aref_t, attr_t,
             and_(
                 (aref_t.c['To attribute'] == attr_t.c.Name),
                 (aref_t.c['To class'] == attr_t.c.Class),
                 (aref_t.c.Domain == attr_t.c.Domain),
             ),
             )
    r = and_(
        (aref_t.c['From attribute'] == attr.name),
        (aref_t.c['From class'] == attr.mmclass),
        (aref_t.c.Domain == attr.domain),
    )
    p = [aref_t.c['To attribute'], aref_t.c['To class'], attr_t.c.Type]  # Project the target attribute and its type
    q = select(p).select_from(j).where(r)
    row = smdb.Connection.execute(q).fetchone()  # There could be many, but we only need one
    refattr = I_Attribute(name=row['To attribute'], mmclass=row['To class'], domain=attr.domain)
    if row['Type'] != '<unresolved>':
        return row['Type']  # The To_attribute has a type
    else:
        return ResolveAttr(attr=refattr)  # The To_attribute is also unresolved. Resolve it!


class Attribute:
    """
    Populate an attribute of a class
    """

    def __init__(self, mmclass, parse_data):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.mmclass = mmclass
        self.parse_data = parse_data
        self.type = parse_data.get('type', "<unresolved>")
        self.identifiers = self.parse_data.get('I', [])  # This attr might not participate in any identifier

        attr_values = dict(
            zip(self.mmclass.domain.model.table_headers['Attribute'],
                [self.parse_data['name'], self.mmclass.name, self.mmclass.domain.name, self.type])
        )
        self.mmclass.domain.model.population['Attribute'].append(attr_values)
        # TODO: Check for derived or non-derived, for now assume the latter
        self.mmclass.domain.model.population['Non Derived Attribute'].append(attr_values)

        for i in self.identifiers:
            # Add Identifier if it is not already in the population
            if i.number not in self.mmclass.identifiers:
                id_values = dict(
                    zip(self.mmclass.domain.model.table_headers['Identifier'],
                        [i.number, self.mmclass.name, self.mmclass.domain.name])
                )
                self.mmclass.domain.model.population['Identifier'].append(id_values)
                if not i.super:
                    self.mmclass.domain.model.population['Irreducible Identifier'].append(id_values)
                else:
                    self.mmclass.domain.model.population['Super Identifier'].append(id_values)
                self.mmclass.identifiers.add(i.number)

            # Include this attribute in the each of its identifiers
            id_attr_values = dict(
                zip(self.mmclass.domain.model.table_headers['Identifier Attribute'],
                    [i.number, self.parse_data['name'], self.mmclass.name, self.mmclass.domain.name])
            )
            self.mmclass.domain.model.population['Identifier Attribute'].append(id_attr_values)
