""" xunit.py - Process a Scrall Execution Unit"""

import logging
from scrall.parse.visitor import Execution_Unit_a, Seq_Statement_Set_a, Comp_Statement_Set_a
from xuml_populate.populate.statement import Statement
from xuml_populate.populate.actions.aparse_types import Activity_ap
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from tkinter import Tk

class ExecutionUnit:
    """
    Process an Execution Unit
    """
    _logger = logging.getLogger(__name__)

    @classmethod
    def process(cls):
        pass

    @classmethod
    def process_statement_set(cls) -> (List[str], List[str]):
        pass

    @classmethod
    def process_output_flow(cls):
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
    def process_method_output_flow(cls, mmdb: 'Tk', ):
        pass

    @classmethod
    def process_method_statement_set(cls, mmdb: 'Tk', activity_data: Activity_ap, statement_set) -> (List[str], List[str]):
        """
        Initiates the population of all elements derived from a set of statements in a method.

        Populates each action and returns two lists of action ids.
        The first list is each action that does not require any data input from any other action
        in the execution unit. These are initial actions since they can execute immediately.

        The second list is each action that does not provide any data input
        to any other action in the execution unit. These are terminal actions.

        :param mmdb:
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
            boundary_actions = Statement.populate(mmdb, activity_data, statement_parse=single_statement)

            pass
        elif block:
            pass
        else:
            # Parsing error, neither were specified
            raise Exception


        # aid = Statement.populate()
        pass
        return boundary_actions

