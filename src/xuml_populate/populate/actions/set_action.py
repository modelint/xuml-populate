"""
set_action.py – Populate a Set Action instance in PyRAL
"""

import logging
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.table import Table
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap
from xuml_populate.exceptions.action_exceptions import (ProductForbidsCommonAttributes, UnjoinableHeaders,
                                                        SetOpRequiresSameHeaders)
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.mm_class import MMclass
from xuml_populate.populate.ns_flow import NonScalarFlow
from xuml_populate.populate.mmclass_nt import Relational_Action_i, Table_Action_i, Set_Action_i
from pyral.relvar import Relvar
from pyral.transaction import Transaction

_logger = logging.getLogger(__name__)

# Transactions
tr_Set_Action = "Set Action"

class SetAction:
    """
    Create all relations for a ProjectAction
    """
    domain = None
    anum = None
    activity_path = None
    scrall_text = None
    action_id = None
    ns_type = None

    @classmethod
    def populate(cls, a_input: Flow_ap, b_input: Flow_ap, setop: str, activity_data: Activity_ap) -> (str, Flow_ap):
        """
        Populate the Set Action

        :param mmdb: The metamodel database
        :param a_input: The a input Non Scalar Flow
        :param b_input: The b input Non Scalar Flow
        :param setop: The set operation name
        :param activity_data:
        :return: Set action output table flow
        """
        # Save attribute values that we will need when creating the various select subsystem
        # classes
        domain = activity_data.domain
        anum = activity_data.anum

        table_header = None
        max_mult = MaxMult.ONE if a_input.max_mult == b_input.max_mult == MaxMult.ONE else MaxMult.MANY
        match setop:
            case 'JOIN':
                _logger.info("Populating JOIN action")
                # The a/b flows are not joinable if the headers share no common attributes
                if NonScalarFlow.headers_disjoint(a_flow=a_input, b_flow=b_input, domain=domain):
                    raise UnjoinableHeaders
                # There is at least one attribute:type in common, so let's take the union to form the new header
                table_header = NonScalarFlow.header_union(a_flow=a_input, b_flow=b_input, domain=domain)
            case 'UNION' | 'INTERSECT' | 'MINUS':
                _logger.info(f"Populating {setop} action")
                # a/b Types must match (same table or same class)
                if not NonScalarFlow.same_headers(a_input, b_input, domain):
                    raise SetOpRequiresSameHeaders
                # Table header can be taken from a or b since they are the same
                if a_input.content == Content.INSTANCE:
                    table_header = MMclass.header(cname=a_input.tname, domain=domain)
                else:
                    table_header = Table.header(tname=a_input.tname, domain=domain)
            case 'TIMES':
                _logger.info("Populating TIMES action")
                # Verify that there are no attributes in common among the a/b flow
                if not NonScalarFlow.headers_disjoint(a_input, b_input, domain=domain):
                    raise ProductForbidsCommonAttributes
                # Now take the union of the disjoint headers as the output
                table_header = NonScalarFlow.header_union(a_flow=a_input, b_flow=b_input, domain=domain)

        # a/b flow inputs are compatible with the spedified operation
        # Populate the output Table Flow and Table (transaction open/close)
        output_tflow = Flow.populate_relation_flow_by_header(table_header=table_header, anum=anum, domain=domain,
                                                             max_mult=max_mult)

        # Create the action (trannsaction open)
        Transaction.open(db=mmdb, name=tr_Set_Action)
        cls.action_id = Action.populate(tr=tr_Set_Action, anum=anum, domain=domain, action_type="set")
        Relvar.insert(db=mmdb, tr=tr_Set_Action, relvar='Relational_Action', tuples=[
            Relational_Action_i(ID=cls.action_id, Activity=anum, Domain=domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Set_Action, relvar='Table_Action', tuples=[
            Table_Action_i(ID=cls.action_id, Activity=anum, Domain=domain, Input_a_flow=a_input.fid,
                           Output_flow=output_tflow.fid)
        ])
        Relvar.insert(db=mmdb, tr=tr_Set_Action, relvar='Set_Action', tuples=[
            Set_Action_i(ID=cls.action_id, Operation=setop, Activity=anum, Domain=domain, Input_b_flow=b_input.fid)
        ])
        Transaction.execute(db=mmdb, name=tr_Set_Action)
        return cls.action_id, output_tflow
