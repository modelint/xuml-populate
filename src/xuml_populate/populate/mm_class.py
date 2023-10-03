"""
mm_class.py – Process parsed class to populate the metamodel db
"""

import logging
from xuml_populate.config import mmdb
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from xuml_populate.populate.element import Element
from xuml_populate.populate.attribute import Attribute
from xuml_populate.populate.mm_type import MMtype
from xuml_populate.populate.mmclass_nt import Class_i, Alias_i

from pyral.relation import Relation

from typing import Dict

_logger = logging.getLogger(__name__)

# Transactions
_tr_Class = "Class"


class MMclass:
    """
    Populate all relevant Class relvars
    """
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
    def header(cls, cname: str, domain: str) -> Dict[str, str]:
        """
        Returns the header for a table reprsentation of this class

        :param cname:   Class name
        :param domain:  Domain name
        :return: The header as a dictionary of attr;type key value pairs
        """
        R = f"Class:<{cname}>, Domain:<{domain}>"
        attrs = Relation.restrict(mmdb, relation='Attribute', restriction=R)
        h = {a['Name']: a['Scalar'] for a in attrs.body}
        return h

    @classmethod
    def exists(cls, cname: str, domain: str) -> bool:
        """

        :param cname:  Name of the class
        :param domain: Its domain name
        :return: True if the class has been populated into this domain
        """
        R = f"Name:<{cname}>, Domain:<{domain}>"
        result = Relation.restrict(mmdb, relation='Class', restriction=R)
        return bool(result.body)



    @classmethod
    def populate(cls, domain: str, subsystem, record):
        """
        Populate a metamodel Class relation

        :param domain:
        :param subsystem:
        :param record:
        :return:
        """

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
        _logger.info(f"Populating class [{cls.name}]")
        _logger.info("Transaction open: Populate class")
        Transaction.open(mmdb, "Class")  # Class, Class Type and Attributes

        # Populate the corresponding Type superclass
        MMtype.populate_class(tr=_tr_Class, cname=cls.name, domain=domain)

        Element.populate_labeled_subys_element(tr=_tr_Class, label=cls.cnum,
                                               subsystem=subsystem.name, domain=domain)
        Relvar.insert(mmdb, tr=_tr_Class, relvar='Class', tuples=[
            Class_i(Name=cls.name, Cnum=cls.cnum, Domain=domain)
        ])
        if cls.alias:
            Relvar.insert(mmdb, tr=_tr_Class, relvar='Alias', tuples=[
                Alias_i(Name=cls.name, Class=cls.name, Domain=domain)
            ])

        # Populate the attributes
        cls.identifiers = set()  # For each newly created class we clear the id set
        for a in cls.record['attributes']:
            Attribute.populate(tr=_tr_Class, domain=domain, cname=cls.name,
                               class_identifiers=cls.identifiers, record=a)

        Transaction.execute(mmdb, _tr_Class)  # Class, Class Type, and Attributes
        _logger.info("Transaction closed: Populate class")
