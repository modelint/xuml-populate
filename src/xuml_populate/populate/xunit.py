""" xunit.py - Process a Scrall Execution Unit"""

import logging
from xuml_populate.config import mmdb
from scrall.parse.visitor import Output_Flow_a
from xuml_populate.populate.actions.aparse_types import Flow_ap, Content, MaxMult
from xuml_populate.populate.statement import Statement
from xuml_populate.populate.actions.aparse_types import Activity_ap
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.populate.actions.expressions.scalar_expr import ScalarExpr
from typing import List

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
            case _:
                pass
        # b, f = ScalarExpr.process(mmdb, rhs=synch_output.output, input_instance_flow=xi_instance_flow,
        #                           activity_data=activity_data)
        pass

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
