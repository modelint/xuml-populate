"""
mm_type.py – Pouplate (metamodel) Type instance
"""

import logging
from typing import TYPE_CHECKING
from class_model_dsl.populate.pop_types import Element_i, Spanning_Element_i, Type_i,\
    Class_Type_i, Scalar_Type_i, Table_Type_i, Table_Attribute_i
from PyRAL.relvar import Relvar

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

    tnums = 0

    @classmethod
    def populate_unknown(cls, mmdb:'Tk', name:str, domain:str):
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
    def populate_scalar(cls, mmdb:'Tk', name:str, domain:str):
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

        cls._logger.info(f"Populating Type <scalar> [{cls.name}]")

        cls.populate_type()
        Relvar.insert(relvar='Scalar_Type', tuples=[
            Scalar_Type_i(Name=cls.name, Domain=cls.domain)
        ])

    @classmethod
    def populate_class(cls, mmdb:'Tk', cname:str, domain:str):
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

        cls._logger.info(f"Populating Type <class> [{cls.name}]")
        cls.populate_type()
        Relvar.insert(relvar='Class_Type', tuples=[
            Class_Type_i(Name=cls.name, Domain=cls.domain)
        ])

    @classmethod
    def populate_type(cls):
        """
        Obtain a Tnum and populate the Type superclass
        """
        cls.tnums += 1
        Tnum =  'T' + (str(cls.tnums))
        Relvar.insert(relvar='Element', tuples=[
            Element_i(Label=Tnum, Domain=cls.domain)
        ])
        Relvar.insert(relvar='Spanning_Element', tuples=[
            Spanning_Element_i(Label=Tnum, Domain=cls.domain)
        ])
        Relvar.insert(relvar='Type', tuples=[
            Type_i(Name=cls.name, Tnum=Tnum, Domain=cls.domain)
        ])