"""
project_action.py – Populate a Project Action instance in PyRAL
"""

import logging
from xuml_populate.exceptions.action_exceptions import ProjectedAttributeNotDefined
from scrall.parse.visitor import Projection_a
from xuml_populate.populate.actions.table import Table
from typing import TYPE_CHECKING
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.mmclass_nt import Relational_Action_i, Table_Action_i, Project_Action_i,\
    Projected_Attribute_i
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class ProjectAction:
    """
    Create all relations for a ProjectAction
    """

    @classmethod
    def populate(cls, mmdb: 'Tk', input_nsflow: Flow_ap, projection: Projection_a,
                 activity_data: Activity_ap) -> Flow_ap:
        """
        Populate the Project Action

        :param mmdb:
        :param input_nsflow: The input Non Scalar Flow that is being projected
        :param projection:  A list of attr names to be projected and optional expansion (ALL, EMPTY)
        :param activity_data:
        :return: Projected table flow
        """
        # Save attribute values that we will need when creating the various select subsystem
        # classes
        domain = activity_data.domain
        anum = activity_data.anum

        _logger.info("Populating projection action")
        table_header = {}
        ns_type = input_nsflow.tname
        # Get type of each attribute
        for pattr in projection.attrs:
            if input_nsflow.content == Content.INSTANCE:
                R = f"Name:<{pattr.name}>, Class:<{input_nsflow.tname}>, Domain:<{domain}>"
                result = Relation.restrict(mmdb, relation='Attribute', restriction=R)
            else:
                R = f"Name:<{pattr.name}>, Table:<{input_nsflow.tname}>, Domain:<{domain}>"
                result = Relation.restrict(mmdb, relation='Table_Attribute', restriction=R)
            if not result.body:
                _logger.error(f"Attribute [{pattr.name}] in projection not defined on class [{input_nsflow.tname}]")
                raise ProjectedAttributeNotDefined
            table_header[pattr.name] = result.body[0]['Scalar']

        # Populate the output Table Flow and Table (transaction open/close)
        output_tflow = Table.populate(mmdb, table_header=table_header, maxmult=input_nsflow.max_mult,
                                      anum=anum, domain=domain)

        # Create the action (trannsaction open)
        action_id = Action.populate(mmdb, anum, domain)
        Relvar.insert(relvar='Relational_Action', tuples=[
            Relational_Action_i(ID=action_id, Activity=anum, Domain=domain)
        ])
        Relvar.insert(relvar='Table_Action', tuples=[
            Table_Action_i(ID=action_id, Activity=anum, Domain=domain, Input_a_flow=input_nsflow.fid,
                           Output_flow=output_tflow.fid)
        ])
        Relvar.insert(relvar='Project_Action', tuples=[
            Project_Action_i(ID=action_id, Activity=anum, Domain=domain)
        ])
        for pattr in projection.attrs:
            Relvar.insert(relvar='Projected_Attribute', tuples=[
                Projected_Attribute_i(Attribute=pattr.name, Non_scalar_type=ns_type, Project_action=action_id,
                                      Activity=anum, Domain=domain)
            ])
        Transaction.execute()
        return output_tflow
