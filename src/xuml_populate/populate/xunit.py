""" xunit.py - Process a Scrall Execution Unit"""

# System
import logging
from typing import List

# Model Integration
from scrall.parse.visitor import Output_Flow_a
from pyral.relvar import Relvar

# Xuml Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, Content, MaxMult
from xuml_populate.populate.statement import Statement
from xuml_populate.populate.actions.aparse_types import Activity_ap
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
    def process(cls):
        pass

    @classmethod
    def process_statement_set(cls) -> (List[str], List[str]):
        pass

    @classmethod
    def process_synch_output(cls, activity_data: Activity_ap, synch_output: Output_Flow_a):
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
                _, _, output_flow = InstanceSet.process(input_instance_flow=xi_instance_flow,
                                                        iset_components=synch_output.output.components,
                                                        activity_data=activity_data)
                pass
            case 'INST_PROJ_a':
                _, _, output_flow = InstanceSet.process(input_instance_flow=xi_instance_flow,
                                                        iset_components=synch_output.output.iset.components,
                                                        activity_data=activity_data)
            case _:
                # Unexpected or unimplemented synch output case
                msg = f"No case for synch output exec unit type: [{type(synch_output.output).__name__}]"
                _logger.error(msg)
                raise UndefinedSynchOutputExecutionUnit(msg)
        # b, f = ScalarExpr.process(mmdb, rhs=synch_output.output, input_instance_flow=xi_instance_flow,
        #                           activity_data=activity_data)

        # Populate the output flow (no transaction required)
        Relvar.insert(db=mmdb, relvar='Synchronous_Output', tuples=[
            Synchronous_Output_i(Anum=activity_data.anum, Domain=activity_data.domain,
                                 Output_flow=output_flow.fid, Type=output_flow.tname)
        ])
        _logger.info(f"INSERT Synchronous operation output flow): ["
                     f"{activity_data.domain}:{activity_data.cname}:{activity_data.opname}:^{output_flow.fid}]")

    @classmethod
    def process_state_statement_set(cls):
        pass

    @classmethod
    def process_operation_output_flow(cls):
        pass

    @classmethod
    def process_operation_statement_set(cls):
        pass

    @classmethod
    def process_method_output_flow(cls):
        pass

    @classmethod
    def process_method_statement_set(cls, activity_data: Activity_ap, statement_set) -> (
            List[str], List[str]):
        """
        Initiates the population of all elements derived from a set of statements in a method.

        Populates each action and returns two lists of action ids.
        The first list is each action that does not require any data input from any other action
        in the execution unit. These are initial actions since they can execute immediately.

        The second list is each action that does not provide any data input
        to any other action in the execution unit. These are terminal actions.

        :param activity_data:
        :param statements:
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
            boundary_actions = Statement.populate(activity_data, statement_parse=single_statement)

            pass
        elif block:
            pass
        else:
            # Parsing error, neither were specified
            raise Exception

        # aid = Statement.populate()
        pass
        return boundary_actions
