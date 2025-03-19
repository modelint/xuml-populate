"""
mm_type.py – Pouplate (metamodel) Type instance
"""

import logging
from xuml_populate.config import mmdb
from xuml_populate.populate.mmclass_nt import Type_i, Scalar_i, Table_i, Table_Attribute_i
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

_logger = logging.getLogger(__name__)

# Transactions
tr_Scalar = "Scalar"
tr_Scalar_Delete = "Scalar Delete"

class MMtype:
    """
    Populate (metamodel) Type instances
    """

    name = None
    domain = None
    mmdb = None
    scalar_types = {}
    class_names = set()

    @classmethod
    def populate_unknown(cls, name: str, domain: str):
        """
        Populate a type that may be Class, Table, or Scalar

        :param name:  The type name
        :param domain: The domain name
        """
        # TODO: For now Table types are not supported
        if name not in cls.class_names:
            cls.populate_scalar(name, domain)

    @classmethod
    def populate_scalar(cls, name: str, domain: str):
        """
        Populate a class type given a class name and domain

        :param name:  Name of a Scalar Type
        :param domain:  Name of its domain
        """
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

        _logger.info(f"Populating Type for scalar [{cls.name}]")

        Transaction.open(mmdb, tr_Scalar)
        Relvar.insert(mmdb, tr=tr_Scalar, relvar='Type', tuples=[
            Type_i(Name=cls.name, Domain=cls.domain)
        ])
        Relvar.insert(mmdb, tr=tr_Scalar, relvar='Scalar', tuples=[
            Scalar_i(Name=cls.name, Domain=cls.domain)
        ])
        Transaction.execute(mmdb, tr_Scalar)


    @classmethod
    def populate_class(cls, tr: str, cname: str, domain: str):
        """
        Populate a class type given a class name and domain

        :param mmdb: The metamodel db name
        :param tr:  The name of the open db transaction
        :param cname:  Name of some class
        :param domain:  Name of its domain
        """
        cls.domain = domain
        cls.name = cname

        cls.class_names.add(cname)

        _logger.info(f"Populating Type for class [{cls.name}]")
        Relvar.insert(mmdb, tr=tr, relvar='Type', tuples=[
            Type_i(Name=cls.name, Domain=cls.domain)
        ])

    @classmethod
    def depopulate_scalar(cls, name: str, domain: str):
        """
        Remove the specified Scalar from the database.

        The only use case for this currently is the removal of the dummy UNRESOLVED Scalar

        :param mmdb: The metamodel db name
        :param name:  The Scalar name
        :param domain:  The domain name
        :return:
        """
        # Verify that the scalar exists
        R = f"Name:<{name}>, Domain:<{domain}>"
        result = Relation.restrict(mmdb, restriction=R, relation="Type").body
        if not result:
            # TODO: This is happening for some reason, but doesn't seem to be an error
            _logger.error("Scalar dummy UNRESOLVED not found during depopulate")
        # Depopulate scalar
        Transaction.open(mmdb, tr_Scalar_Delete)
        Relvar.deleteone(mmdb, tr=tr_Scalar_Delete, relvar_name='Type', tid={'Name': name, 'Domain': domain})
        Relvar.deleteone(mmdb, tr=tr_Scalar_Delete, relvar_name='Scalar', tid={'Name': name, 'Domain': domain})
        Transaction.execute(mmdb, tr_Scalar_Delete)
