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
                        Column('Alias', Text, nullable=False, primary_key=False),
                        PrimaryKeyConstraint('Name', name='I'),
                        UniqueConstraint('Alias', name='I2'),
                        ),
        'Modeled Domain': Table('Modeled Domain', db.MetaData,
                                Column('Name', Text, nullable=False, primary_key=True),
                                PrimaryKeyConstraint('Name', name='I'),
                                ForeignKeyConstraint(('Name',), ['Domain.Name', ], name='R4'),
                                ),
        'Domain Partition': Table('Domain Partition', db.MetaData,
                                  Column('Number', Integer, nullable=False, primary_key=True),
                                  Column('Domain', Text, nullable=False, primary_key=True),
                                  PrimaryKeyConstraint('Number', 'Domain', name='I'),
                                  ForeignKeyConstraint(('Domain',), ['Domain.Name', ], name='R3'),
                                  ),
        'Element': Table('Element', db.MetaData,
                         Column('Number', Text, nullable=False, primary_key=True),
                         Column('Domain', Text, nullable=False, primary_key=True),
                         PrimaryKeyConstraint('Number', 'Domain', name='I'),
                         ForeignKeyConstraint(('Domain',), ['Domain.Name', ], name='R15'),
                         ),
        'Subsystem': Table('Subsystem', db.MetaData,
                           Column('Name', Text, nullable=False, primary_key=True),
                           Column('First element number', Integer, nullable=False, primary_key=False),
                           Column('Domain', Text, nullable=False, primary_key=True),
                           Column('Alias', Text, nullable=False, primary_key=False),
                           PrimaryKeyConstraint('Name', 'Domain', name='I'),
                           UniqueConstraint('Alias', 'Domain', name='I2'),
                           UniqueConstraint('First element number', 'Domain', name='I3'),
                           ForeignKeyConstraint(('Domain',), ['Domain.Name', ], name='R3'),
                           ),
        'Subsystem Element': Table('Subsystem Element', db.MetaData,
                                   Column('Number', Text, nullable=False, primary_key=True),
                                   Column('Domain', Text, nullable=False, primary_key=True),
                                   Column('Subsystem', Text, nullable=False, primary_key=False),
                                   PrimaryKeyConstraint('Number', 'Domain', name='I'),
                                   ForeignKeyConstraint(('Number', 'Domain',), ['Element.Number', 'Element.Domain', ],
                                                        name='R16'),
                                   ForeignKeyConstraint(('Subsystem', 'Domain',),
                                                        ['Subsystem.Name', 'Subsystem.Domain', ], name='R13'),
                                   ),
        'Spanning Element': Table('Spanning Element', db.MetaData,
                                  Column('Number', Text, nullable=False, primary_key=True),
                                  Column('Domain', Text, nullable=False, primary_key=True),
                                  PrimaryKeyConstraint('Number', 'Domain', name='I'),
                                  ForeignKeyConstraint(('Number', 'Domain',), ['Element.Number', 'Element.Domain', ],
                                                       name='R16'),
                                  ),
        'Class': Table('Class', db.MetaData,
                       Column('Name', Text, nullable=False, primary_key=True),
                       Column('Cnum', Text, nullable=False, primary_key=False),
                       Column('Domain', Text, nullable=False, primary_key=True),
                       PrimaryKeyConstraint('Name', 'Domain', name='I'),
                       UniqueConstraint('Cnum', 'Domain', name='I2'),
                       ForeignKeyConstraint(('Domain',), ['Domain.Name', ], name='R14'),
                       ),
        'Alias': Table('Alias', db.MetaData,
                       Column('Name', Text, nullable=False, primary_key=True),
                       Column('Class', Text, nullable=False, primary_key=False),
                       Column('Domain', Text, nullable=False, primary_key=True),
                       PrimaryKeyConstraint('Name', 'Domain', name='I'),
                       ForeignKeyConstraint(('Class', 'Domain',), ['Class.Name', 'Class.Domain', ], name='R29'),
                       UniqueConstraint('Class', 'Domain', name='I2'),
                       ),
        'Attribute': Table('Attribute', db.MetaData,
                           Column('Name', Text, nullable=False, primary_key=True),
                           Column('Class', Text, nullable=False, primary_key=True),
                           Column('Domain', Text, nullable=False, primary_key=True),
                           Column('Type', Text, nullable=False, primary_key=False),
                           PrimaryKeyConstraint('Name', 'Class', 'Domain', name='I'),
                           ForeignKeyConstraint(('Class', 'Domain',), ['Class.Name', 'Class.Domain', ], name='R20'),
                           ),
        'Non Derived Attribute': Table('Non Derived Attribute', db.MetaData,
                                       Column('Name', Text, nullable=False, primary_key=True),
                                       Column('Class', Text, nullable=False, primary_key=True),
                                       Column('Domain', Text, nullable=False, primary_key=True),
                                       PrimaryKeyConstraint('Name', 'Class', 'Domain', name='I'),
                                       ForeignKeyConstraint(('Name', 'Class', 'Domain',),
                                                            ['Attribute.Name', 'Attribute.Class', 'Attribute.Domain', ],
                                                            name='R25'),
                                       ),
        'Identifier': Table('Identifier', db.MetaData,
                            Column('Number', Integer, nullable=False, primary_key=True),
                            Column('Class', Text, nullable=False, primary_key=True),
                            Column('Domain', Text, nullable=False, primary_key=True),
                            PrimaryKeyConstraint('Number', 'Class', 'Domain', name='I'),
                            ForeignKeyConstraint(('Class', 'Domain',), ['Class.Name', 'Class.Domain', ], name='R27'),
                            ),
        'Irreducible Identifier': Table('Irreducible Identifier', db.MetaData,
                                        Column('Number', Integer, nullable=False, primary_key=True),
                                        Column('Class', Text, nullable=False, primary_key=True),
                                        Column('Domain', Text, nullable=False, primary_key=True),
                                        PrimaryKeyConstraint('Number', 'Class', 'Domain', name='I'),
                                        ForeignKeyConstraint(('Number', 'Class', 'Domain',),
                                                             ['Identifier.Number', 'Identifier.Class',
                                                              'Identifier.Domain', ], name='R30'),
                                        ForeignKeyConstraint(('Class', 'Domain',), ['Class.Name', 'Class.Domain', ],
                                                             name='R31'),
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
        'Relationship': Table('Relationship', db.MetaData,
                              Column('Rnum', Text, nullable=False, primary_key=True),
                              Column('Domain', Text, nullable=False, primary_key=True),
                              PrimaryKeyConstraint('Rnum', 'Domain', name='I'),
                              ForeignKeyConstraint(('Rnum', 'Domain',),
                                                   ['Subsystem Element.Number', 'Subsystem Element.Domain'],
                                                   name='R14'),
                              ),
        'Association': Table('Association', db.MetaData,
                             Column('Rnum', Text, nullable=False, primary_key=True),
                             Column('Domain', Text, nullable=False, primary_key=True),
                             PrimaryKeyConstraint('Rnum', 'Domain', name='I'),
                             ForeignKeyConstraint(('Rnum', 'Domain',),
                                                  ['Relationship.Rnum', 'Relationship.Domain'],
                                                  name='R100'),
                             ),
        'Generalization': Table('Generalization', db.MetaData,
                                Column('Rnum', Text, nullable=False, primary_key=True),
                                Column('Domain', Text, nullable=False, primary_key=True),
                                Column('Superclass', Text, nullable=True, primary_key=False),
                                # Superclass temporarily nullable, see Issue 2 in issue tracker
                                PrimaryKeyConstraint('Rnum', 'Domain', name='I'),
                                ForeignKeyConstraint(('Rnum', 'Domain',),
                                                     ['Relationship.Rnum', 'Relationship.Domain'], name='R100'),
                                ),
        'Facet': Table('Facet', db.MetaData,
                       Column('Rnum', Text, nullable=False, primary_key=True),
                       Column('Class', Text, nullable=False, primary_key=True),
                       Column('Domain', Text, nullable=False, primary_key=True),
                       PrimaryKeyConstraint('Rnum', 'Class', 'Domain', name='I'),
                       ForeignKeyConstraint(('Rnum', 'Domain',),
                                            ['Generalization.Rnum', 'Generalization.Domain'], name='R101_gen'),
                       ForeignKeyConstraint(('Class', 'Domain',),
                                            ['Class.Name', 'Class.Domain'], name='R101_class'),
                       ),
        'Superclass': Table('Superclass', db.MetaData,
                            Column('Rnum', Text, nullable=False, primary_key=True),
                            Column('Class', Text, nullable=False, primary_key=True),
                            Column('Domain', Text, nullable=False, primary_key=True),
                            PrimaryKeyConstraint('Rnum', 'Class', 'Domain', name='I'),
                            ForeignKeyConstraint(('Rnum', 'Class', 'Domain',),
                                                 ['Facet.Rnum', 'Facet.Class', 'Facet.Domain'], name='R102'),
                            ),
        'Subclass': Table('Subclass', db.MetaData,
                          Column('Rnum', Text, nullable=False, primary_key=True),
                          Column('Class', Text, nullable=False, primary_key=True),
                          Column('Domain', Text, nullable=False, primary_key=True),
                          PrimaryKeyConstraint('Rnum', 'Class', 'Domain', name='I'),
                          ForeignKeyConstraint(('Rnum', 'Class', 'Domain',),
                                               ['Facet.Rnum', 'Facet.Class', 'Facet.Domain'], name='R102'),
                          ),
        'Minimal Partition': Table('Minimal Partition', db.MetaData,
                                   Column('Rnum', Text, nullable=False, primary_key=True),
                                   Column('Domain', Text, nullable=False, primary_key=True),
                                   Column('A subclass', Text, nullable=False, primary_key=False),
                                   Column('B subclass', Text, nullable=False, primary_key=False),
                                   PrimaryKeyConstraint('Rnum', 'Domain', name='I'),
                                   ForeignKeyConstraint(('Rnum', 'A subclass', 'Domain',),
                                                        ['Subclass.Rnum', 'Subclass.Class', 'Subclass.Domain'],
                                                        name='R117'),
                                   ForeignKeyConstraint(('Rnum', 'B subclass', 'Domain',),
                                                        ['Subclass.Rnum', 'Subclass.Class', 'Subclass.Domain'],
                                                        name='R118'),
                                   ),
        'Lineage': Table('Lineage', db.MetaData,
                         Column('Lnum', Text, nullable=False, primary_key=True),
                         Column('Domain', Text, nullable=False, primary_key=True),
                         PrimaryKeyConstraint('Lnum', 'Domain', name='I'),
                         ForeignKeyConstraint(('Lnum', 'Domain',),
                                              ['Spanning Element.Number', 'Spanning Element.Domain'],
                                              name='R17'),
                         ),
        'Class in Lineage': Table('Class in Lineage', db.MetaData,
                                  Column('Class', Text, nullable=False, primary_key=True),
                                  Column('Lnum', Text, nullable=False, primary_key=True),
                                  Column('Domain', Text, nullable=False, primary_key=True),
                                  PrimaryKeyConstraint('Class', 'Lnum', 'Domain', name='I'),
                                  ForeignKeyConstraint(('Class', 'Domain',),
                                                       ['Class.Name', 'Class.Domain'],
                                                       name='R131_class'),
                                  ForeignKeyConstraint(('Lnum', 'Domain',),
                                                       ['Lineage.Lnum', 'Lineage.Domain'],
                                                       name='R131_lin'),
                                  ),
        'Binary Association': Table('Binary Association', db.MetaData,
                                    Column('Rnum', Text, nullable=False, primary_key=True),
                                    Column('Domain', Text, nullable=False, primary_key=True),
                                    PrimaryKeyConstraint('Rnum', 'Domain', name='I'),
                                    ForeignKeyConstraint(('Rnum', 'Domain',),
                                                         ['Association.Rnum', 'Association.Domain'],
                                                         name='R119'),
                                    ),
        'Perspective': Table('Perspective', db.MetaData,
                             Column('Side', Text, nullable=False, primary_key=True),
                             Column('Rnum', Text, nullable=False, primary_key=True),
                             Column('Domain', Text, nullable=False, primary_key=True),
                             Column('Viewed class', Text, nullable=False, primary_key=False),
                             Column('Phrase', Text, nullable=False, primary_key=False),
                             Column('Conditional', Boolean, nullable=False, primary_key=False),
                             Column('Multiplicity', Text, nullable=False, primary_key=False),
                             PrimaryKeyConstraint('Side', 'Rnum', 'Domain', name='I'),
                             PrimaryKeyConstraint('Rnum', 'Domain', 'Phrase', name='I2'),
                             ForeignKeyConstraint(('Viewed class', 'Domain',),
                                                  ['Class.Name', 'Class.Domain'], name='R110'),
                             ),
        'Asymmetric Perspective': Table('Asymmetric Perspective', db.MetaData,
                                        Column('Side', Text, nullable=False, primary_key=True),
                                        Column('Rnum', Text, nullable=False, primary_key=True),
                                        Column('Domain', Text, nullable=False, primary_key=True),
                                        PrimaryKeyConstraint('Side', 'Rnum', 'Domain', name='I'),
                                        ForeignKeyConstraint(('Side', 'Rnum', 'Domain',),
                                                             ['Perspective.Side', 'Perspective.Rnum',
                                                              'Perspective.Domain'], name='R121'),
                                        ),
        'T Perspective': Table('T Perspective', db.MetaData,
                               Column('Rnum', Text, nullable=False, primary_key=True),
                               Column('Domain', Text, nullable=False, primary_key=True),
                               PrimaryKeyConstraint('Rnum', 'Domain', name='I'),
                               ForeignKeyConstraint(('Rnum', 'Domain',),
                                                    ['Asymmetric Perspective.Rnum',
                                                     'Asymmetric Perspective.Domain'], name='R105'),
                               ForeignKeyConstraint(('Rnum', 'Domain',),
                                                    ['Binary Association.Rnum',
                                                     'Binary Association.Domain'], name='R124'),
                               ),
        'P Perspective': Table('P Perspective', db.MetaData,
                               Column('Rnum', Text, nullable=False, primary_key=True),
                               Column('Domain', Text, nullable=False, primary_key=True),
                               PrimaryKeyConstraint('Rnum', 'Domain', name='I'),
                               ForeignKeyConstraint(('Rnum', 'Domain',),
                                                    ['Asymmetric Perspective.Rnum',
                                                     'Asymmetric Perspective.Domain'], name='R105'),
                               ForeignKeyConstraint(('Rnum', 'Domain',),
                                                    ['Binary Association.Rnum',
                                                     'Binary Association.Domain'], name='R125'),
                               ),
        'Formalizing Class Role': Table('Formalizing Class Role', db.MetaData,
                                        Column('Rnum', Text, nullable=False, primary_key=True),
                                        Column('Class', Text, nullable=False, primary_key=True),
                                        Column('Domain', Text, nullable=False, primary_key=True),
                                        PrimaryKeyConstraint('Rnum', 'Class', 'Domain', name='I'),
                                        ForeignKeyConstraint(('Rnum', 'Domain',),
                                                             ['Relationship.Rnum',
                                                              'Relationship.Domain'], name='R150_Rel'),
                                        ForeignKeyConstraint(('Class', 'Domain',),
                                                             ['Class.Name',
                                                              'Class.Domain'], name='R150_Class'),
                                        ),
        'Association Class': Table('Association Class', db.MetaData,
                                   Column('Rnum', Text, nullable=False, primary_key=True),
                                   Column('Class', Text, nullable=False, primary_key=False),
                                   Column('Domain', Text, nullable=False, primary_key=True),
                                   PrimaryKeyConstraint('Rnum', 'Domain', name='I'),
                                   UniqueConstraint('Class', 'Domain', name='I2'),
                                   ForeignKeyConstraint(('Rnum', 'Domain',),
                                                        ['Association.Rnum',
                                                         'Association.Domain'], name='R120_Association'),
                                   ForeignKeyConstraint(('Class', 'Domain',),
                                                        ['Class.Name',
                                                         'Class.Domain'], name='R120_Class'),
                                   ForeignKeyConstraint(('Rnum', 'Class', 'Domain',),
                                                        ['Formalizing Class Role.Rnum', 'Formalizing Class Role.Class',
                                                         'Formalizing Class Role.Domain'], name='R151'),
                                   ),
        'Reference': Table('Reference', db.MetaData,
                           Column('Ref', Text, nullable=False, primary_key=True),
                           Column('From class', Text, nullable=False, primary_key=True),
                           Column('To class', Text, nullable=False, primary_key=True),
                           Column('Rnum', Text, nullable=False, primary_key=True),
                           Column('Domain', Text, nullable=False, primary_key=True),
                           PrimaryKeyConstraint('Ref', 'From class', 'To class', 'Rnum', 'Domain', name='I'),
                           ForeignKeyConstraint(('From class', 'Rnum', 'Domain',),
                                                ['Formalizing Class Role.Class', 'Formalizing Class Role.Rnum',
                                                 'Formalizing Class Role.Domain'], name='R155_Form_CRole'),
                           ForeignKeyConstraint(('To class', 'Domain',),
                                                ['Class.Name', 'Class.Domain'], name='R155_Class'),
                           ),
        'Attribute Reference': Table('Attribute Reference', db.MetaData,
                                     Column('From attribute', Text, nullable=False, primary_key=True),
                                     Column('From class', Text, nullable=False, primary_key=True),
                                     Column('To attribute', Text, nullable=False, primary_key=True),
                                     Column('To class', Text, nullable=False, primary_key=True),
                                     Column('Domain', Text, nullable=False, primary_key=True),
                                     Column('Rnum', Text, nullable=False, primary_key=True),
                                     Column('Ref', Text, nullable=False, primary_key=False),
                                     Column('To identifier', Integer, nullable=False, primary_key=False),
                                     PrimaryKeyConstraint('From attribute', 'From class', 'To attribute', 'To class',
                                                          'Domain', 'Rnum', name='I'),
                                     UniqueConstraint('From attribute', 'From class', 'Ref', 'Rnum', 'Domain',
                                                      name='I2'),
                                     ForeignKeyConstraint(('From attribute', 'From class', 'Domain',),
                                                          ['Attribute.Name',
                                                           'Attribute.Class', 'Attribute.Domain', ],
                                                          name='R21_Attr'),
                                     ForeignKeyConstraint(('To identifier', 'To attribute', 'To class', 'Domain',),
                                                          ['Identifier Attribute.Identifier',
                                                           'Identifier Attribute.Attribute',
                                                           'Identifier Attribute.Class',
                                                           'Identifier Attribute.Domain', ], name='R21_Id'),
                                     ForeignKeyConstraint(('Ref', 'From class', 'To class', 'Rnum', 'Domain',),
                                                          ['Reference.Ref', 'Reference.From class',
                                                           'Reference.To class', 'Reference.Rnum',
                                                           'Reference.Domain', ], name='R23'),
                                     ),
        'Referring Class': Table('Referring Class', db.MetaData,
                                 Column('Rnum', Text, nullable=False, primary_key=True),
                                 Column('Class', Text, nullable=False, primary_key=True),
                                 Column('Domain', Text, nullable=False, primary_key=True),
                                 PrimaryKeyConstraint('Rnum', 'Class', 'Domain', name='I'),
                                 ForeignKeyConstraint(('Rnum', 'Class', 'Domain',),
                                                      ['Formalizing Class Role.Rnum', 'Formalizing Class Role.Class',
                                                       'Formalizing Class Role.Domain', ], name='R151'),
                                 ),
        'Generalization Reference': Table('Generalization Reference', db.MetaData,
                                          Column('Subclass', Text, nullable=False, primary_key=True),
                                          Column('Superclass', Text, nullable=False, primary_key=True),
                                          Column('Rnum', Text, nullable=False, primary_key=True),
                                          Column('Domain', Text, nullable=False, primary_key=True),
                                          PrimaryKeyConstraint('Subclass', 'Superclass', 'Rnum', 'Domain',
                                                               name='I'),
                                          ForeignKeyConstraint(('Superclass', 'Subclass', 'Rnum', 'Domain',),
                                                               ['Reference.From class', 'Reference.To class',
                                                                'Reference.Rnum', 'Reference.Domain'], name='R152'),
                                          ForeignKeyConstraint(('Subclass', 'Rnum', 'Domain',),
                                                               ['Subclass.Class', 'Subclass.Rnum', 'Subclass.Domain', ],
                                                               name='R156'),
                                          ForeignKeyConstraint(('Superclass', 'Rnum', 'Domain',),
                                                               ['Superclass.Class', 'Superclass.Rnum',
                                                                'Superclass.Domain', ], name='R170'),
                                          ),
        'Association Reference': Table('Association Reference', db.MetaData,
                                       Column('Ref type', Text, nullable=False, primary_key=True),
                                       Column('From class', Text, nullable=False, primary_key=True),
                                       Column('To class', Text, nullable=False, primary_key=True),
                                       Column('Rnum', Text, nullable=False, primary_key=True),
                                       Column('Domain', Text, nullable=False, primary_key=True),
                                       Column('Perspective', Text, nullable=False, primary_key=False),
                                       PrimaryKeyConstraint('Ref type', 'From class', 'To class', 'Rnum', 'Domain',
                                                            name='I'),
                                       ForeignKeyConstraint(('Ref type', 'From class', 'To class', 'Rnum', 'Domain',),
                                                            ['Reference.Ref', 'Reference.From class',
                                                             'Reference.To class', 'Reference.Rnum',
                                                             'Reference.Domain'], name='R152'),
                                       ForeignKeyConstraint(('Rnum', 'Domain', 'Perspective',),
                                                            ['Perspective.Rnum', 'Perspective.Domain',
                                                             'Perspective.Side'], name='R154'),
                                       ),
        'Simple Association Reference': Table('Simple Association Reference', db.MetaData,
                                              Column('From class', Text, nullable=False, primary_key=True),
                                              Column('To class', Text, nullable=False, primary_key=True),
                                              Column('Rnum', Text, nullable=False, primary_key=True),
                                              Column('Domain', Text, nullable=False, primary_key=True),
                                              PrimaryKeyConstraint('From class', 'To class', 'Rnum', 'Domain',
                                                                   name='I'),
                                              ForeignKeyConstraint(
                                                  ('From class', 'To class', 'Rnum', 'Domain',),
                                                  ['Association Reference.From class',
                                                   'Association Reference.To class', 'Association Reference.Rnum',
                                                   'Association Reference.Domain'], name='R176'),
                                              ForeignKeyConstraint(
                                                  ('From class', 'Rnum', 'Domain',),
                                                  ['Referring Class.Class', 'Referring Class.Rnum',
                                                   'Referring Class.Domain'], name='R157'),
                                              ),
        'Association Class Reference': Table('Association Class Reference', db.MetaData,
                                             Column('Ref type', Text, nullable=False, primary_key=True),
                                             Column('Association class', Text, nullable=False, primary_key=True),
                                             Column('Participating class', Text, nullable=False, primary_key=True),
                                             Column('Rnum', Text, nullable=False, primary_key=True),
                                             Column('Domain', Text, nullable=False, primary_key=True),
                                             PrimaryKeyConstraint('Ref type', 'Association class',
                                                                  'Participating class', 'Rnum',
                                                                  'Domain', name='I'),
                                             ForeignKeyConstraint(
                                                 ('Ref type', 'Association class', 'Participating class', 'Rnum',
                                                  'Domain',),
                                                 ['Association Reference.Ref type',
                                                  'Association Reference.From class',
                                                  'Association Reference.To class', 'Association Reference.Rnum',
                                                  'Association Reference.Domain'], name='R176'),
                                             ),
        'T Reference': Table('T Reference', db.MetaData,
                             Column('Association class', Text, nullable=False, primary_key=True),
                             Column('Participating class', Text, nullable=False, primary_key=True),
                             Column('Rnum', Text, nullable=False, primary_key=True),
                             Column('Domain', Text, nullable=False, primary_key=True),
                             PrimaryKeyConstraint('Association class', 'Participating class', 'Rnum',
                                                  'Domain', name='I'),
                             ForeignKeyConstraint(
                                 ('Association class', 'Participating class', 'Rnum', 'Domain',),
                                 ['Association Class Reference.Association class',
                                  'Association Class Reference.Participating class', 'Association Class Reference.Rnum',
                                  'Association Class Reference.Domain'], name='R153'),
                             ForeignKeyConstraint(
                                 ('Rnum', 'Domain',),
                                 ['Association Class.Rnum', 'Association Class.Domain'], name='R158'),
                             ),
        'P Reference': Table('P Reference', db.MetaData,
                             Column('Association class', Text, nullable=False, primary_key=True),
                             Column('Participating class', Text, nullable=False, primary_key=True),
                             Column('Rnum', Text, nullable=False, primary_key=True),
                             Column('Domain', Text, nullable=False, primary_key=True),
                             PrimaryKeyConstraint('Association class', 'Participating class', 'Rnum',
                                                  'Domain', name='I'),
                             ForeignKeyConstraint(
                                 ('Association class', 'Participating class', 'Rnum', 'Domain',),
                                 ['Association Class Reference.Association class',
                                  'Association Class Reference.Participating class', 'Association Class Reference.Rnum',
                                  'Association Class Reference.Domain'], name='R153'),
                             ForeignKeyConstraint(
                                 ('Rnum', 'Domain',),
                                 ['Association Class.Rnum', 'Association Class.Domain'], name='R159'),
                             ),
    }
