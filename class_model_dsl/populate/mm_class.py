"""
mm_class.py – Convert parsed class to a relation
"""

import logging
from PyRAL.transaction import Transaction
from PyRAL.relvar import Relvar
from class_model_dsl.populate.element import Element
from class_model_dsl.populate.attribute import Attribute
from class_model_dsl.populate.method import Method
from class_model_dsl.populate.ee import EE
from class_model_dsl.populate.mm_type import MMtype
from class_model_dsl.populate.pop_types import Class_i, Alias_i

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tkinter import Tk



class MMclass:
    """
    Create a class relation
    """
    _logger = logging.getLogger(__name__)
    record = None
    name = None
    alias = None
    cnum = None
    identifiers = None
    attributes = None
    methods = None
    ee = None
    ee_ops = None

    @classmethod
    def populate(cls, mmdb: 'Tk', domain: str, subsystem, record):
        """Constructor"""

        cls.record = record
        cls.name = record['name']
        cls.attributes = record['attributes']
        cls.alias = record.get('alias')  # Optional
        cls.methods = record.get('methods')
        cls.ee = record.get('ee')
        cls.ee_ops = record.get('ee_ops')

        # Get the next cnum
        cls.cnum = subsystem.next_cnum()
        #
        # Populate class
        cls._logger.info(f"Populating class [{cls.name}]")
        cls._logger.info("Transaction open: Populate class")
        Transaction.open(tclral=mmdb) # Class, Class Type and Attributes

        # Populate the required Class Type
        MMtype.populate_class(mmdb, cname=cls.name, domain=domain)

        Element.populate_labeled_subys_element(mmdb, label=cls.cnum, subsystem_name=subsystem.name, domain_name=domain)
        Relvar.insert(relvar='Class', tuples=[
            Class_i(Name=cls.name, Cnum=cls.cnum, Domain=domain)
        ])
        if cls.alias:
            Relvar.insert(relvar='Alias', tuples=[
                Alias_i(Name=cls.name, Class=cls.name, Domain=domain)
            ])

        # Populate the attributes
        cls.identifiers = set()  # For each newly created class we clear the id set
        for a in cls.record['attributes']:
            Attribute.populate(mmdb=mmdb, domain=domain, cname=cls.name,
                               class_identifiers=cls.identifiers, record=a)

        Transaction.execute() # Class, Class Type, and Attributes
        cls._logger.info("Transaction closed: Populate class")
