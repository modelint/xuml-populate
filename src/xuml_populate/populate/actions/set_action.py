"""
set_action.py – Populate a Set Action instance in PyRAL
"""

import logging
from scrall.parse.visitor import Projection_a
from xuml_populate.populate.actions.table import Table
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content
from xuml_populate.exceptions.action_exceptions import (ProductForbidsCommonAttributes, UnjoinableHeaders,
                                                        SetOpRequiresSameHeaders)
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Relational_Action_i, Table_Action_i, Set_Action_i
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
    def populate(cls, mmdb: 'Tk', a_input: Flow_ap, b_input: Flow_ap, setop: str, anum: str,
                 domain: str, activity_path: str, scrall_text: str) -> Flow_ap:
        """
        Populate the Set Action

        :param mmdb: The metamodel database
        :param a_input: The a input Non Scalar Flow
        :param b_input: The b input Non Scalar Flow
        :param setop: The set operation name
        :param anum: Activity number
        :param domain: Domain
        :param scrall_text:
        :param activity_path:
        :return: Set action output table flow
        """
        # Save attribute values that we will need when creating the various select subsystem
        # classes
        cls.mmdb = mmdb
        cls.domain = domain
        cls.anum = anum
        cls.activity_path = activity_path
        cls.scrall_text = scrall_text

        table_header = {}
        match setop:
            case 'JOIN':
                # Reject if inputs a and b are not joinable
                # This means that there must be at least one attribute/type pair in common
                if a_input.content == Content.INSTANCE:
                    R = f"Class:<{a_input.tname}>, Domain:<{cls.domain}>"
                    Relation.restrict(cls.mmdb, relation='Attribute', restriction=R)
                else:
                    R = f"Table:<{a_input.tname}>, Domain:<{cls.domain}>"
                    Relation.restrict(cls.mmdb, relation='Table_Attribute', restriction=R)
                Relation.project(cls.mmdb, attributes=('Name', 'Scalar'), svar_name='a_nt')
                Relation.project(cls.mmdb, attributes=('Name',), relation='a_nt', svar_name='a_n')
                if b_input.content == Content.INSTANCE:
                    R = f"Class:<{b_input.tname}>, Domain:<{cls.domain}>"
                    Relation.restrict(cls.mmdb, relation='Attribute', restriction=R)
                else:
                    R = f"Table:<{b_input.tname}>, Domain:<{cls.domain}>"
                    Relation.restrict(cls.mmdb, relation='Table_Attribute', restriction=R)
                Relation.project(cls.mmdb, attributes=('Name', 'Scalar'), svar_name='b_nt')
                Relation.project(cls.mmdb, attributes=('Name',), relation='b_nt', svar_name='b_n')
                # TODO: Take the intersection of the a_n, b_n -> common_names
                # TODO: if a_nt, b_nt each restricted on common_names are equal, success
                # TODO: update metamodel so that Attribute.Type is renamed to .Scalar
                # TODO: implement intersection and is (equality) in PyRAL
                # TODO: Table header is the union of a_nt and b_nt (if joinable)
            case 'UNION' | 'INTERSECT' | 'MINUS':
                # produce a_nt and b_nt and test equality
                # a/b Types must match (same table or same class)
                # TODO: Take the set of attributes in a_nt as the table header
                print()
            case 'TIMES':
                # produce a_nt and b_nt and take the intersection
                # if empty, success
                # TODO: Table header is the union of a_nt and b_nt
                print()

        # Inputs are compatible with the operation

        # Populate the output Table Flow and Table (transaction open/close)

        output_tflow = Table.populate(mmdb, table_header=table_header, anum=anum, domain=domain)

        # Create the action (trannsaction open)
        cls.action_id = Action.populate(mmdb, anum, domain)
        Relvar.insert(relvar='Relational_Action', tuples=[
            Relational_Action_i(ID=cls.action_id, Activity=anum, Domain=domain)
        ])
        Relvar.insert(relvar='Table_Action', tuples=[
            Table_Action_i(ID=cls.action_id, Activity=anum, Domain=domain, Input_a_flow=input_nsflow.fid,
                           Output_flow=output_tflow.fid)
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
        return output_tflow
