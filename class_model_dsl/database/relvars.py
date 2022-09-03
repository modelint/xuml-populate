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
        'class': Table('Class', db.MetaData,
                       Column('Name', Text, nullable=False, primary_key=True),
                       PrimaryKeyConstraint('Name', name='I'),
                       ),
        'attribute': Table('Attribute', db.MetaData,
                           Column('Name', Text, nullable=False, primary_key=True),
                           Column('Class', Text, nullable=False, primary_key=True),
                           ForeignKeyConstraint(('Class',), ['Class.Name', ], name='R20'),
                           ),
    }
