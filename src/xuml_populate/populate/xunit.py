""" xunit.py - Process a Scrall Execution Unit"""

# System
import logging
from typing import TYPE_CHECKING, List

# Model Integration
from scrall.parse.visitor import Output_Flow_a, Seq_Statement_Set_a, Comp_Statement_Set_a
from pyral.relvar import Relvar
from pyral.relation import Relation

# Xuml Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity

from xuml_populate.utility import print_mmdb
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, Content, MaxMult
from xuml_populate.populate.statement import Statement
from xuml_populate.populate.actions.aparse_types import ActivityAP, Boundary_Actions
from xuml_populate.populate.actions.scalar_assignment import ScalarExpr
from xuml_populate.populate.actions.extract_action import ExtractAction
from xuml_populate.populate.actions.read_action import ReadAction
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.populate.mmclass_nt import Synchronous_Output_i
from xuml_populate.populate.actions.type_selector import TypeSelector
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
    def process_synch_output(cls, activity: 'Activity', synch_output: Output_Flow_a) -> Boundary_Actions:
        """

        :param activity:
        :param synch_output:  Output flow execution unit parse
        :return:
        """
        actions_in = set()
        actions_out = set()
        cls.activity = activity
        output_type = type(synch_output.output).__name__
        output_flow = None
        ain = None
        aout = None
        match output_type:
            case 'INST_a':
                iset = InstanceSet(iset_components=synch_output.output.components,
                                   activity=activity)
                ain, aout, output_flow = iset.process()
                pass
            case 'INST_PROJ_a':
                iset = InstanceSet(iset_components=synch_output.output.iset.components,
                                   activity=activity, input_instance_flow=activity.xiflow)
                ain, aout, output_flow = iset.process()
                if synch_output.output.projection:
                    p = synch_output.output.projection
                    # Get the type of this method's output
                    method_output_type = activity.domain_method_output_types[activity.anum]
                    # If it is scalar, verify that we have a tuple or a single instance before the projection
                    R = f"Name:<{method_output_type.name}>, Domain:<{activity.domain}>"
                    scalar_r = Relation.restrict(db=mmdb, relation="Scalar", restriction=R)
                    if scalar_r.body:
                        if output_flow.content == Content.SCALAR:
                            msg = (f"Cannot project on a scalar flow {output_flow} outputing from method"
                                   f" {activity.activity_path}")
                            _logger.error(msg)
                            raise ActionException(msg)
                        if output_flow.max_mult != MaxMult.ONE:
                            msg = f"Cannot project on many inst/tuple flow at {activity.activity_path}"
                            _logger.error(msg)
                            raise ActionException(msg)
                        if output_flow.content == Content.RELATION:
                            # Make sure there aren't zero projected attrs
                            if not p.attrs:
                                msg = (f"Projection requires at least one attribute to output a scalar value at"
                                       f" {activity.activity_path}")
                                _logger.error(msg)
                                raise ActionException(msg)
                            # Make sure there is exactly one, in fact
                            if len(p.attrs) > 1:
                                msg = (f"Projecting on multiple attributes but there is only one scalar output value at"
                                       f" {activity.activity_path}")
                                _logger.error(msg)
                                raise ActionException(msg)
                            xa = ExtractAction(tuple_flow=output_flow, attr=p.attrs[0].name, activity=activity)
                            aout, xa_flow = xa.populate()
                            pass
                        else:
                            # must be an instance flow
                            ra = ReadAction(input_single_instance_flow=output_flow, attrs=(p.attrs[0].name,),
                                            anum=activity.anum, domain=activity.domain)
                            ra_id, ra_flow = ra.populate()
                            pass

                    # and that we output a single value
                    #If we output a table, we just do a project and output the table
                    # If we output an instance ref, we should first do an instance assignment in a prior statement
                    # before returning
                    pass
                pass
            case 'N_a':
                iset = InstanceSet(iset_components=[synch_output.output],
                                   activity=activity)
                ain, aout, output_flow = iset.process()
                if not output_flow:
                    # Must be a scalar flow
                    se = ScalarExpr(expr=synch_output.output, input_instance_flow=activity.xiflow,
                                    activity=activity)
                    _, sflows = se.process()
                    if not sflows:
                        msg = (f"No output flow found for synch output {synch_output} in scalar expression"
                               f" at {activity.activity_path}")
                        _logger.error(msg)
                        raise ActionException(msg)
                    if len(sflows) == 1:
                        output_flow = sflows[0]
                    else:
                        # TODO: Handle case where a method outputs multiple scalar flows
                        msg = (f"Multiple scalar output flows in synch output {synch_output} in scalar expression"
                               f" at {activity.activity_path}")
                        _logger.error(msg)
                        raise IncompleteActionException(msg)
                    pass
            case 'Type_expr_a':
                ta = TypeSelector(scalar=synch_output.output.type.name, value=synch_output.output.selector, activity=activity)
                ain, aout, output_flow = ta.populate()
            case 'MATH_a' | 'BOOL_a':
                se = ScalarExpr(expr=synch_output.output, input_instance_flow=activity.xiflow, activity=activity)
                bactions, scalar_flows = se.process()
                if not scalar_flows:
                    msg = f"Synch output scalar flow not found in scalar expression at {activity.activity_path}"
                    _logger.error(msg)
                    raise ActionException(msg)
                if len(scalar_flows) > 1:
                    # TODO: Handle multiple scalar flows in synch output from scalar expression
                    msg = f"Synch output multiple scalar flows not yet handled {activity.activity_path}"
                    _logger.error(msg)
                    raise IncompleteActionException(msg)
                output_flow = scalar_flows[0]
            case _:
                # Unexpected or unimplemented synch output case
                msg = f"No case for synch output exec unit type: [{type(synch_output.output).__name__}]"
                _logger.error(msg)
                raise UndefinedSynchOutputExecutionUnit(msg)
        # b, f = ScalarExpr.process(mmdb, rhs=synch_output.output, input_instance_flow=xi_instance_flow,
        #                           activity=activity)

        # Add the output flow to this Activity's set so they can be resolved to a single output later
        activity.synch_output_flows.add(output_flow)
        if ain:
            actions_in.add(ain)
        if aout:
            actions_out.add(aout)
        Boundary_actions = Boundary_Actions(ain=actions_in, aout=actions_out)
        return Boundary_actions



    @classmethod
    def process_statement_set(cls, content: Seq_Statement_Set_a | Comp_Statement_Set_a | Output_Flow_a,
                              activity: "Activity") -> Boundary_Actions:
        """
        Initiates the population of all elements derived from a set of statements in an Activity.

        Populates each action and returns two lists of action ids.
        The first list is each action that does not require any data input from any other action
        in the execution unit. These are initial_pseudo_state actions since they can execute immediately.

        The second list is each action that does not provide any data input
        to any other action in the execution unit. These are terminal actions.

        Args:
            content: execution_unit content is a set of one or more statements or blocks or an output_flow
            activity: The enclosing Activity

        Returns:
            Tuple with a list of initial_pseudo_state and terminal actions
        """
        # Let's first check to see if we have an output_flow
        if type(content.statement).__name__ == 'Output_Flow_a':
            boundary_actions = ExecutionUnit.process_synch_output(synch_output=content.statement, activity=activity)
            return boundary_actions

        # Its a statement_set

        single_statement = content.statement
        block = content.block
        boundary_actions = None

        # Mutually exclusive options
        if block and single_statement:
            # Parsing error, cannot have both
            raise Exception

        if single_statement:
            boundary_actions = Statement.populate(activity=activity, statement_parse=single_statement)

        elif block:
            ain: set[str] = set()
            aout: set[str] = set()
            for count, s in enumerate(block):
                b = ExecutionUnit.process_statement_set(content=s.statement_set, activity=activity)
                ain.update(b.ain)
                aout.update(b.aout)
            boundary_actions = Boundary_Actions(ain=ain, aout=aout)

            pass  # TODO: Look at the b list and figure out what to return based on example
        else:
            # Parsing error, neither were specified
            raise Exception

        # aid = Statement.populate()
        pass
        return boundary_actions

