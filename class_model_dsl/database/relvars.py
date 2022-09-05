"""
relvars.py -- SM Metamodel DB relational variable definitions

    This file defines all relvars (relational variables) for the SM Metamodel database. In SQL terms,
    this is the schema definition for the database. These relvars are derived from the SM Metamodel.
"""
from sqlalchemy import Table, Column, Text, String, Integer, Boolean, Enum, Float
from sqlalchemy import ForeignKey, UniqueConstraint, PrimaryKeyConstraint, ForeignKeyConstraint, CheckConstraint


def define(db) -> dict:
    """
    Define all the relvars in the Shlaer-Mellor Metamodel Database.

    :param db: A SM meta database class which provides an Sqlalchemy MetaData attribute
    :return: Dictionary of table name key, table schema value pairs
    """
    return {
        # Just a class to get started
        'Domain': Table('Domain', db.MetaData,
                        Column('Name', Text, nullable=False, primary_key=True),
                        PrimaryKeyConstraint('Name', name='I'),
                        ),
        'Class': Table('Class', db.MetaData,
                       Column('Name', Text, nullable=False, primary_key=True),
                       Column('Domain', Text, nullable=False, primary_key=True),
                       PrimaryKeyConstraint('Name', 'Domain', name='I'),
                       ForeignKeyConstraint(('Domain',), ['Domain.Name', ], name='R14'),
                       ),
        'Attribute': Table('Attribute', db.MetaData,
                           Column('Name', Text, nullable=False, primary_key=True),
                           Column('Class', Text, nullable=False, primary_key=True),
                           Column('Domain', Text, nullable=False, primary_key=True),
                           PrimaryKeyConstraint('Name', 'Class', 'Domain', name='I'),
                           ForeignKeyConstraint(('Class', 'Domain',), ['Class.Name', 'Class.Domain', ], name='R20'),
                           ),
        'Identifier': Table('Identifier', db.MetaData,
                            Column('Number', Integer, nullable=False, primary_key=True),
                            Column('Class', Text, nullable=False, primary_key=True),
                            Column('Domain', Text, nullable=False, primary_key=True),
                            PrimaryKeyConstraint('Number', 'Class', 'Domain', name='I'),
                            ForeignKeyConstraint(('Class', 'Domain',), ['Class.Name', 'Class.Domain', ], name='R27'),
                            ),
        'Identifier Attribute': Table('Identifier Attribute', db.MetaData,
                                      Column('Identifier', Integer, nullable=False, primary_key=True),
                                      Column('Attribute', Text, nullable=False, primary_key=True),
                                      Column('Class', Text, nullable=False, primary_key=True),
                                      Column('Domain', Text, nullable=False, primary_key=True),
                                      PrimaryKeyConstraint('Identifier', 'Attribute', 'Class', 'Domain', name='I'),
                                      ForeignKeyConstraint(('Attribute', 'Class', 'Domain',),
                                                           ['Attribute.Name', 'Attribute.Class', 'Attribute.Domain', ],
                                                           name='R22_Attribute'),
                                      ForeignKeyConstraint(('Identifier', 'Class', 'Domain',),
                                                           ['Identifier.Number', 'Identifier.Class',
                                                            'Identifier.Domain', ],
                                                           name='R22_Identifier'),
                                      ),
    }
