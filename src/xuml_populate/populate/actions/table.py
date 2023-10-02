""" table.py - Define a table """

import logging
from typing import TYPE_CHECKING, Tuple, Dict
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.aparse_types import Flow_ap
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from pyral.relation import Relation
from xuml_populate.populate.mmclass_nt import Table_i, Type_i, Table_Attribute_i, Model_Attribute_i
from xuml_populate.populate.actions.aparse_types import MaxMult

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class Table:
    """
    Populates the Table and all unconditionally related classes.
    This includes Table Attribute, Model Attribute and Table Flow
    """

    @classmethod
    def header(cls, mmdb: 'Tk', tname: str, domain: str) -> Dict[str, str]:
        """
        Returns the header for this table type

        :param mmdb:
        :param tname:   Class name
        :param domain:  Domain name
        :return:  Dictionary of attr:scalar (type) values
        """
        R = f"Table:<{tname}>, Domain:<{domain}>"
        attrs = Relation.restrict(mmdb, relation='Table_Attribute', restriction=R)
        h = {a['Name']: a['Scalar'] for a in attrs.body}
        return h

    @classmethod
    def populate(cls, mmdb: 'Tk', table_header: Dict[str, str], maxmult: MaxMult, anum: str, domain: str) -> Flow_ap:
        """

        :param mmdb:
        :param table_header:
        :param maxmult:  The multplicity of the source flow
        :param anum:
        :param domain:
        :return:
        """

        # Generate a table name by converting the table_header into one long string
        # with attribute/types delimited by underscores
        table_name = "_".join([f"{k}_{v}" for k, v in table_header.items()])

        # Check to see if the table already exists, if so, just create the table flow
        # using the existing Table instance (name)
        R = f"Name:<{table_name}>, Domain:<{domain}>"
        result = Relation.restrict(mmdb, relation='Table', restriction=R)
        if result.body:
            _logger.info(f"Populating flow on existing Table: [{table_name}]")
            Transaction.open(mmdb)  # Table type
            table_flow = Flow.populate_table_flow(mmdb, activity=anum, tname=table_name, domain=domain,
                                                  is_tuple=True if maxmult == MaxMult.ONE else False, label=None)
            Transaction.execute()
            return table_flow

        _logger.info(f"Populating Table flow on existing Table: [{table_name}]")
        Transaction.open(mmdb)  # Table type
        # A Table can't exist without a flow
        table_flow = Flow.populate_table_flow(mmdb, activity=anum, tname=table_name, domain=domain,
                                              is_tuple=True if maxmult == MaxMult.ONE else False, label=None)
        Relvar.insert(relvar='Table', tuples=[
            Table_i(table_name, domain)
        ])
        Relvar.insert(relvar='Type', tuples=[
            Type_i(table_name, domain)
        ])
        for a, t in table_header.items():
            Relvar.insert(relvar='Table_Attribute', tuples=[
                Table_Attribute_i(Name=a, Table=table_name, Domain=domain, Scalar=t)
            ])
            Relvar.insert(relvar='Model_Attribute', tuples=[
                Model_Attribute_i(Name=a, Non_scalar_type=table_name, Domain=domain)
            ])
        Transaction.execute()
        return table_flow

