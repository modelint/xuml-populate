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
from xuml_populate.populate.mmclass_nt import Synchronous_Output_i
from xuml_populate.exceptions.action_exceptions import *

tr_OutputFlow = "OutputFlow"

_logger = logging.getLogger(__name__)


class ExecutionUnit:
    """
    Process a Scrall execution_unit

    Note: Unlike metamodel classes, Scrall grammar element names are lowercase with underscore delimiters.
    So we write execution_unit instead of "Execution Unit" since it is merely a Scrall specific construct.

    The Scrall grammar defines an execution_unit as a statement_set followed by any number of sequence tokens.

    A statement_set can be either a sequenced_statement_set or a component_statement_set.

    A sequenced_statement_set is a possibly mixed sequence of statements and blocks, and a block is a sequence
    of one or more execution_units. So we'll need recursion to process these. This, by the way, is called
    'sequenced' because they can be enabled by any number of sequence_tokens (handled outside this class).

    A component_statement_set is exactly the same as a sequenced_statement_set except that it is internal to some
    statement, like a switch or a decision, and thus cannot be preceded by any sequence_tokens.

    And since we don't deal with the sequence_tokens here, we'll handle both sequenced_statement_sets and
    component_statement_sets identically.

    To sum up, we take either a sequenced or component statement set
    """

    @classmethod
    def process_synch_output(cls, activity_data: ActivityAP, synch_output: Output_Flow_a):
        """

        :param activity_data:
        :param synch_output:  Output flow execution unit parse
        :return:
        """
        cls.activity_data = activity_data
        match type(synch_output.output).__name__:
            case 'INST_a':
                iset = InstanceSet(iset_components=synch_output.output.components,
                                   activity_data=activity_data)
                _, _, output_flow = iset.process()
                pass
            case 'INST_PROJ_a':
                iset = InstanceSet(iset_components=synch_output.output.iset.components,
                                   activity_data=activity_data)
                _, _, output_flow = iset.process()
            case 'N_a':
                iset = InstanceSet(iset_components=[synch_output.output],
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
    def process_statement_set(cls, content: Seq_Statement_Set_a | Comp_Statement_Set_a | Output_Flow_a,
                              activity_data: ActivityAP) -> Boundary_Actions:
        """
        Initiates the population of all elements derived from a set of statements in an Activity.

        Populates each action and returns two lists of action ids.
        The first list is each action that does not require any data input from any other action
        in the execution unit. These are initial actions since they can execute immediately.

        The second list is each action that does not provide any data input
        to any other action in the execution unit. These are terminal actions.

        Args:
            content: execution_unit content is a set of one or more statements or blocks or an output_flow
            activity_data: Info about the activity and its unparsed text. Useful for providing helpful error msgs

        Returns:
            Tuple with a list of initial and terminal actions
        """
        # Let's first check to see if we have an output_flow
        if type(content.statement).__name__ == 'Output_Flow_a':
            ExecutionUnit.process_synch_output(synch_output=content.statement, activity_data=activity_data)
            return Boundary_Actions(ain=set(), aout=set())

        # Its a statement_set

        single_statement = content.statement
        block = content.block
        boundary_actions = None

        # Mutually exclusive options
        if block and single_statement:
            # Parsing error, cannot have both
            raise Exception

        if single_statement:
            boundary_actions = Statement.populate(activity_data=activity_data, statement_parse=single_statement)

        elif block:
            ba_list = list()
            for count, s in enumerate(block):
                b = ExecutionUnit.process_statement_set(content=s.statement_set, activity_data=activity_data)
                ba_list.append(b)
            pass  # TODO: Look at the b list and figure out what to return based on example
        else:
            # Parsing error, neither were specified
            raise Exception

        # aid = Statement.populate()
        pass
        return boundary_actions

