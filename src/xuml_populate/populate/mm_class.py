"""
mm_class.py – Convert parsed class to a relation
"""

import logging
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from xuml_populate.populate.element import Element
from xuml_populate.populate.attribute import Attribute
from xuml_populate.populate.mm_type import MMtype
from xuml_populate.populate.mmclass_nt import Class_i, Alias_i

from pyral.relation import Relation

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tkinter import Tk



class MMclass:
    """
    Create a class relation
    """
    _logger = logging.getLogger(__name__)
    mmdb = None
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
    def exists(cls, cname:str, domain:str) -> bool:
        """

        :param cname:  Name of the class
        :param domain: Its domain name
        :return: True if the class has been populated into this domain
        """
        R = f"Name:<{cname}>, Domain:<{domain}>"
        result = Relation.restrict(cls.mmdb, relation='Class', restriction=R)
        return bool(result.body)



    @classmethod
    def populate(cls, mmdb: 'Tk', domain: str, subsystem, record):
        """Constructor"""

        cls.mmdb = mmdb
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
        Transaction.open(tclral=mmdb)  # Class, Class Type and Attributes

        # Populate the corresponding Type superclass
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

        Transaction.execute()  # Class, Class Type, and Attributes
        cls._logger.info("Transaction closed: Populate class")
