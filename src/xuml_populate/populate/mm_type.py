"""
mm_type.py – Pouplate (metamodel) Type instance
"""

import logging
from typing import TYPE_CHECKING
from xuml_populate.populate.mmclass_nt import Type_i, Scalar_i, Table_i, Table_Attribute_i
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

if TYPE_CHECKING:
    from tkinter import Tk

class MMtype:
    """
    Populate (metamodel) Type instances
    """
    _logger = logging.getLogger(__name__)

    name = None
    domain = None
    mmdb = None
    scalar_types = {}
    class_names = set()

    @classmethod
    def populate_unknown(cls, mmdb: 'Tk', name: str, domain: str):
        """
        Populate a type that may be Class, Table, or Scalar

        :param mmdb:
        :param name:
        :param domain:
        """
        # TODO: For now Table types are not supported
        if name not in cls.class_names:
            cls.populate_scalar(mmdb, name, domain)

    @classmethod
    def populate_scalar(cls, mmdb: 'Tk', name: str, domain: str):
        """
        Populate a class type given a class name and domain

        :param mmdb:  metamodel db
        :param name:  Name of a Scalar Type
        :param domain:  Name of its domain
        """
        cls.mmdb = mmdb
        cls.domain = domain
        cls.name = name

        # Determine if this type has already been defined
        if domain not in cls.scalar_types:
            cls.scalar_types[domain] = set()

        if name in cls.scalar_types[domain]:
            # This type has already been populated
            return

        # Add it to the set of defined scalar types so that we don't populated it more than once
        cls.scalar_types[domain].add(name)

        cls._logger.info(f"Populating Type for scalar [{cls.name}]")

        Relvar.insert(relvar='Type', tuples=[
            Type_i(Name=cls.name, Domain=cls.domain)
        ])
        Relvar.insert(relvar='Scalar', tuples=[
            Scalar_i(Name=cls.name, Domain=cls.domain)
        ])

    @classmethod
    def populate_class(cls, mmdb: 'Tk', cname: str, domain: str):
        """
        Populate a class type given a class name and domain

        :param mmdb:  metamodel db
        :param cname:  Name of some class
        :param domain:  Name of its domain
        """
        cls.mmdb = mmdb
        cls.domain = domain
        cls.name = cname

        cls.class_names.add(cname)

        cls._logger.info(f"Populating Type for class [{cls.name}]")
        Relvar.insert(relvar='Type', tuples=[
            Type_i(Name=cls.name, Domain=cls.domain)
        ])

    @classmethod
    def depopulate_scalar_type(cls, mmdb: 'Tk', name: str, domain: str):
        """
        Remove the specified type from the database.

        The only use case for this currently is the removal of the dummy UNRESOLVED Scalar
        :param mmdb:
        :param name:
        :param domain:
        :return:
        """
        # Get the element label
        R = f"Name:<{name}>, Domain:<{domain}>"
        result = Relation.restrict(mmdb, restriction=R, relation="Type").body
        if not result:
            cls._logger.error("Unresolved attr type not found during depopulate")
        Transaction.open(mmdb)
        Relvar.deleteone(mmdb, 'Type', {'Name': name, 'Domain': domain}, defer=True)
        Relvar.deleteone(mmdb, 'Scalar', {'Name': name, 'Domain': domain}, defer=True)
        # Depopulate element
        Transaction.execute()
        # Relation.print(mmdb)

