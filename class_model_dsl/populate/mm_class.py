"""
mm_class.py – Convert parsed class to a relation
"""

import logging
from collections import namedtuple
from PyRAL.transaction import Transaction
from PyRAL.relvar import Relvar
# from class_model_dsl.populate.attribute import Attribute

Element_i = namedtuple('Element_i', 'Number Domain')
Subsystem_Element_i = namedtuple('Element_i', 'Number Domain Subsystem')
Class_i = namedtuple('Class_i', 'Name Cnum Domain')
Alias_i = namedtuple('Alias_i', 'Name Class Domain')
Attribute_i = namedtuple('Attribute_i', 'Name Class Domain Type')
Identiifer_i = namedtuple('Identifier_i', 'Number Class Domain')
Identifer_Attribute_i = namedtuple('Identifier_Attribute_i', 'Identifier Attribute Class Domain')

class MMclass:
    """
    Create a class relation
    """
    _logger = logging.getLogger(__name__)
    record = None
    name = None
    attributes = None
    identifiers = set()
    alias = None
    cnum = None


    @classmethod
    def populate(cls, mmdb, domain, subsystem, record):
        """Constructor"""

        cls.record = record
        cls.name = record['name']
        cls.attributes = record['attributes']
        cls.alias = record.get('alias')  # Optional

        # Get the next cnum
        cls.cnum = subsystem.next_cnum()
        #
        # Populate class
        cls._logger.info(f"Populating class [{cls.name}]")
        Transaction.open(db=mmdb)
        Relvar.insert(db=mmdb, relvar='Element', tuples=[
            Element_i(Number=cls.cnum, Domain=domain['name'])
        ])
        Relvar.insert(db=mmdb, relvar='Subsystem_Element', tuples=[
            Subsystem_Element_i(Number=cls.cnum, Domain=domain['name'], Subsystem=subsystem.name)
        ])
        Relvar.insert(db=mmdb, relvar='Class', tuples=[
            Class_i(Name=cls.name, Cnum=cls.cnum, Domain=domain['name'])
        ])
        if cls.alias:
            Relvar.insert(db=mmdb, relvar='Alias', tuples=[
                Alias_i(Name=cls.name, Class=cls.name, Domain=domain['name'])
            ])
        pass


        #
        # for a in self.attributes:
        #     Attribute(mmclass=self, parse_data=a)