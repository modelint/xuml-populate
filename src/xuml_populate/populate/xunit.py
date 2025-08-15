""" xunit.py - Process a Scrall Execution Unit"""

# System
import logging
from typing import List

# Model Integration
from scrall.parse.visitor import Output_Flow_a, Seq_Statement_Set_a, Comp_Statement_Set_a
from pyral.relvar import Relvar

# Xuml Populate
from xuml_populate.utility import print_mmdb
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, Content, MaxMult
from xuml_populate.populate.statement import Statement
from xuml_populate.populate.actions.aparse_types import ActivityAP, Boundary_Actions
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.populate.actions.expressions.scalar_expr import ScalarExpr
from xuml_populate.populate.mmclass_nt import Synchronous_Output_i
from xuml_populate.exceptions.action_exceptions import *

tr_OutputFlow = "OutputFlow"

_logger = logging.getLogger(__name__)

class ExecutionUnit:
    """
    Process an Execution Unit
    """

    @classmethod
    def process(cls, activity_data: ActivityAP, statement_set: Seq_Statement_Set_a | Comp_Statement_Set_a
                ) -> Boundary_Actions:
        """

        Args:
            activity_data:
            statement_set:

        Returns:

        """

    @classmethod
    def process_synch_output(cls, activity_data: ActivityAP, synch_output: Output_Flow_a):
        """

        :param activity_data:
        :param synch_output:  Output flow execution unit parse
        :return:
        """
        cls.activity_data = activity_data
        xi_instance_flow = Flow_ap(fid=activity_data.xiflow, content=Content.INSTANCE, tname=activity_data.cname,
                                   max_mult=MaxMult.ONE)
        match type(synch_output.output).__name__:
            case 'INST_a':
                iset = InstanceSet(input_instance_flow=xi_instance_flow,
                                   iset_components=synch_output.output.components,
                                   activity_data=activity_data)
                _, _, output_flow = iset.process()
                pass
            case 'INST_PROJ_a':
                iset = InstanceSet(input_instance_flow=xi_instance_flow,
                                   iset_components=synch_output.output.iset.components,
                                   activity_data=activity_data)
                _, _, output_flow = iset.process()
            case _:
                # Unexpected or unimplemented synch output case
                msg = f"No case for synch output exec unit type: [{type(synch_output.output).__name__}]"
                _logger.error(msg)
                raise UndefinedSynchOutputExecutionUnit(msg)
        # b, f = ScalarExpr.process(mmdb, rhs=synch_output.output, input_instance_flow=xi_instance_flow,
        #                           activity_data=activity_data)


        # Populate the output flow (no transaction required)
        Relvar.insert(db=mmdb, relvar='Synchronous Output', tuples=[
            Synchronous_Output_i(Anum=activity_data.anum, Domain=activity_data.domain,
                                 Output_flow=output_flow.fid, Type=output_flow.tname)
        ])
        _logger.info(f"INSERT Synchronous operation output flow): ["
                     f"{activity_data.activity_path}:^{output_flow.fid}]")

    @classmethod
    def process_statement_set(cls, activity_data: ActivityAP,
                              statement_set: Seq_Statement_Set_a | Comp_Statement_Set_a) -> Boundary_Actions:
        """
        Initiates the population of all elements derived from a set of statements in an Activity.

        Populates each action and returns two lists of action ids.
        The first list is each action that does not require any data input from any other action
        in the execution unit. These are initial actions since they can execute immediately.

        The second list is each action that does not provide any data input
        to any other action in the execution unit. These are terminal actions.

        :param activity_data:  Info about the activity and its unparsed text. Useful for providing helpful error msgs
        :param statement_set:  The statement set we are populating
        :return: Tuple with a list of initial and terminal actions
        """
        single_statement = statement_set.statement
        block = statement_set.block
        boundary_actions = None

        # Mutually exclusive options
        if block and single_statement:
            # Parsing error, cannot have both
            raise Exception

        if single_statement:
            boundary_actions = Statement.populate(activity_data=activity_data, statement_parse=single_statement)

            pass
        elif block:
            ba_list = list()
            for s in block:
                b = ExecutionUnit.process_statement_set(statement_set=s.statement_set, activity_data=activity_data)
                ba_list.append(b)
            pass
        else:
            # Parsing error, neither were specified
            raise Exception

        # aid = Statement.populate()
        pass
        return boundary_actions
