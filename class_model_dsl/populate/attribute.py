"""
attribute.py – Create an attribute relation
"""

import logging
from class_model_dsl.database.sm_meta_db import SMmetaDB as smdb
from sqlalchemy import select, join, func, and_
from collections import namedtuple

I_Attribute = namedtuple('_I_Attribute', 'name, mmclass, domain')


def ResolveAttrTypes():
    """
    Update all unresolved attribute types
    """
    attr_t = smdb.MetaData.tables['Attribute']
    p = [attr_t.c.Name, attr_t.c.Class, attr_t.c.Domain]
    q = select(p).where(attr_t.c.Type == "<unresolved>")
    rows = smdb.Connection.execute(q).fetchall()
    uattrs = [I_Attribute(*r) for r in rows]
    for uattr in uattrs:
        assign_type = ResolveAttr(attr=uattr)
        r = and_(
            (attr_t.c.Name == uattr.name),
            (attr_t.c.Class == uattr.mmclass),
            (attr_t.c.Domain == uattr.domain),
        )
        u = attr_t.update().where(r).values(Type=assign_type)
        smdb.Connection.execute(u)
    print()


def ResolveAttr(attr: I_Attribute) -> str:
    """

    :return:  Type name
    """
    # Select one attribute reference where the attribute is the source
    aref_t = smdb.MetaData.tables['Attribute Reference']
    attr_t = smdb.MetaData.tables['Attribute']
    j = join(aref_t, attr_t, aref_t.c['To attribute'] == attr_t.c.Name, aref_t.c['To class'] == attr_t.c.Class)
    r = and_(
        (aref_t.c['From attribute'] == attr.name),
        (aref_t.c['From class'] == attr.mmclass),
        (aref_t.c.Domain == attr.domain),
    )
    p = [aref_t.c['To attribute'], aref_t.c['To class'], attr_t.c.Type]  # Get the target attribute
    q = select(p).select_from(j).where(r)
    row = smdb.Connection.execute(q).fetchone()
    refattr = I_Attribute(name=row['To attribute'], mmclass=row['To class'], domain=attr.domain)
    if row['Type'] != '<unresolved>':
        return row['Type']
    else:
        ResolveAttr(attr=refattr)


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
