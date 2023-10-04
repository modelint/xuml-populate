""" table.py - Define a table """

import logging
from typing import Tuple, Dict
from xuml_populate.config import mmdb
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from pyral.relation import Relation
from xuml_populate.populate.mmclass_nt import Table_i, Type_i, Table_Attribute_i, Model_Attribute_i

_logger = logging.getLogger(__name__)

class Table:
    """
    Populates the Table and all unconditionally related classes.
    This includes Table Attribute, Model Attribute and Table Flow
    """

    @classmethod
    def header(cls, tname: str, domain: str) -> Dict[str, str]:
        """
        Returns the header for this table type

        :param tname:   Class name
        :param domain:  Domain name
        :return:  Dictionary of attr:scalar (type) values
        """
        R = f"Table:<{tname}>, Domain:<{domain}>"
        attrs = Relation.restrict(mmdb, relation='Table_Attribute', restriction=R)
        h = {a['Name']: a['Scalar'] for a in attrs.body}
        return h

    @classmethod
    def populate(cls, tr: str, table_header: Dict[str, str], domain: str) -> str:
        """
        Population happens in the context of a Relation Flow transaction.

        :param tr: The Relaton Flow transaction name
        :param table_header: A dictionary of attribute name;type pairs
        :param domain: The domain name
        :return: The name of the Table
        """
        # Generate a table name by converting the table_header into one long string
        # with attribute name/types delimited by underscores
        table_name = "_".join([f"{attr_name}_{attr_type}" for attr_name, attr_type in table_header.items()])

        # Check to see if the table already exists, if so, just return the name
        R = f"Name:<{table_name}>, Domain:<{domain}>"
        result = Relation.restrict(mmdb, relation='Table', restriction=R)
        if result.body:
            return table_name

        _logger.info(f"Populating Table flow on existing Table: [{table_name}]")
        # A Table can't exist without a flow
        Transaction.open(mmdb, tr)  # Table type
        Relvar.insert(mmdb, tr=tr, relvar='Table', tuples=[
            Table_i(table_name, domain)
        ])
        Relvar.insert(mmdb, tr=tr, relvar='Type', tuples=[
            Type_i(table_name, domain)
        ])
        for a, t in table_header.items():
            Relvar.insert(mmdb, tr=tr, relvar='Table_Attribute', tuples=[
                Table_Attribute_i(Name=a, Table=table_name, Domain=domain, Scalar=t)
            ])
            Relvar.insert(mmdb, tr=tr, relvar='Model_Attribute', tuples=[
                Model_Attribute_i(Name=a, Non_scalar_type=table_name, Domain=domain)
            ])
        return table_name

