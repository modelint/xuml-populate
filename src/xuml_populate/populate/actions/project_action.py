"""
project_action.py – Populate a Project Axtion instance in PyRAL
"""

import logging
from xuml_populate.exceptions.action_exceptions import ProjectedAttributeNotDefined
from scrall.parse.visitor import Projection_a
from xuml_populate.populate.actions.table import Table
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from xuml_populate.populate.actions.aparse_types import TableFlow_ap, InstanceFlow_ap, MaxMult
from xuml_populate.exceptions.action_exceptions import ComparingNonAttributeInSelection, NoInputInstanceFlow
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Relational_Action_i, Table_Action_i, Project_Action_i,\
    Projected_Attribute_i
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction
from scrall.parse.visitor import N_a, BOOL_a, Op_a

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class ProjectAction:
    """
    Create all relations for a ProjectAction
    """
    mmdb = None
    domain = None
    anum = None
    activity_path = None
    scrall_text = None
    action_id = None
    ns_type = None

    @classmethod
    def populate(cls, mmdb: 'Tk', input_nsflow: InstanceFlow_ap | TableFlow_ap, projection: Projection_a, anum: str,
                 domain: str, activity_path: str, scrall_text: str) -> TableFlow_ap:
        """
        Populate the Project Action

        :param mmdb:
        :param anum:
        :param domain:
        :param input_nsflow: The input Non Scalar Flow that is being projected
        :param projection:  A list of attr names to be projected and optional expansion (ALL, EMPTY)
        :param scrall_text:
        :param activity_path:
        :return: Projected table flow
        """
        # Save attribute values that we will need when creating the various select subsystem
        # classes
        cls.mmdb = mmdb
        cls.domain = domain
        cls.anum = anum
        cls.activity_path = activity_path
        cls.scrall_text = scrall_text

        _logger.info("")
        table_header = {}
        match type(input_nsflow).__name__:
            case 'InstanceFlow_ap':
                cls.ns_type = input_nsflow.ctype
                # Get type of each attribute
                for pattr in projection.attrs:
                    R = f"Name:<{pattr.name}>, Class:<{input_nsflow.ctype}>, Domain:<{cls.domain}>"
                    result = Relation.restrict3(cls.mmdb, relation='Attribute', restriction=R)
                    if not result.body:
                        _logger.error(f"Attribute [{pattr.name}] in projection not defined on class [{input_nsflow.ctype}]")
                        raise ProjectedAttributeNotDefined
                    table_header[pattr.name] = result.body[0]['Type']
            case 'TableFlow_ap':
                cls.ns_type = input_nsflow.ttype
                # TODO: Add this case for projecting on a table input
                print()

        # Populate the output Table Flow and Table (transaction open/close)
        output_tflow_id = Table.populate(mmdb, table_header=table_header, anum=anum, domain=domain)

        # Create the action (trannsaction open)
        cls.action_id = Action.populate(mmdb, anum, domain)
        Relvar.insert(relvar='Relational_Action', tuples=[
            Relational_Action_i(ID=cls.action_id, Activity=anum, Domain=domain)
        ])
        Relvar.insert(relvar='Table_Action', tuples=[
            Table_Action_i(ID=cls.action_id, Activity=anum, Domain=domain, Input_a_flow=input_nsflow.fid,
                           Output_flow=output_tflow_id)
        ])
        Relvar.insert(relvar='Project_Action', tuples=[
            Relational_Action_i(ID=cls.action_id, Activity=anum, Domain=domain)
        ])
        for pattr in projection.attrs:
            Relvar.insert(relvar='Projected_Attribute', tuples=[
                Projected_Attribute_i(Attribute=pattr.name, Non_scalar_type=cls.ns_type, Project_action=cls.action_id,
                                      Activity=anum, Domain=domain)
            ])
        Transaction.execute()
        pass
