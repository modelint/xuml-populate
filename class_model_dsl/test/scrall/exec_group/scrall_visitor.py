""" scrall_visitor.py - exec_group test """
from arpeggio import PTNodeVisitor
from collections import namedtuple
from class_model_dsl.sp_exceptions import ScrallCallWithoutOperation, ScrallMissingParameterName
import logging

_logger = logging.getLogger(__name__)

# Here we define named tuples that we use to package up the parsed data
# and return in the visit result.
Supplied_Parameter_a = namedtuple('Supplied_Parameter_a', 'pname sval')
"""Parameter name and flow name pair for a set of supplied parameters"""
Op_a = namedtuple('Op_a', 'op_name supplied_params')
Call_a = namedtuple('Call_a', 'subject ops')
"""The subject of a call could be an instance set (method) or an external entity (ee operation)"""
Attr_Access_a = namedtuple('Attr_Access_a', 'cname attr')
Selection_a = namedtuple('Selection_a', 'card criteria')
Inst_Assignment_a = namedtuple('Inst_Assignment_a', 'lhs card rhs')
Signal_a = namedtuple('Signal_a', 'event supplied_params dest')
"""Signal sent to trigger event at destination with optional supplied parameters"""
Signal_Action_a = namedtuple('Signal_Action_a', 'event supplied_params dest delay')
Block_a = namedtuple('Block_a', 'actions')
Sequence_Token_a = namedtuple('Sequence_Token_a', 'name')
Execution_Unit_a = namedtuple('Execution_Unit_a', 'input_tokens output_tokens action_group')
Decision_a = namedtuple('Decision_a', 'input true_result false_result')
Delete_Action_a = namedtuple('Delete_Action_a', 'instance_set')
Case_a = namedtuple('Case_a', 'enums execution_unit')
Scalar_Switch_a = namedtuple('Scalar_Switch_a', 'scalar_input_flow cases')
MATH_a = namedtuple('MATH_a', 'op operands')
UNARY_a = namedtuple('UNARY_a', 'op operand')
BOOL_a = namedtuple('BOOL_a', 'op operands')
Scalar_Assignment_a = namedtuple('Scalar_Assignment_a', 'lhs rhs')
PATH_a = namedtuple('PATH_a', 'hops')
INST_a = namedtuple('INST_a', 'components')
R_a = namedtuple('R_a', 'rnum')

class ScrallVisitor(PTNodeVisitor):
    """
    Based on Arpeggio's generic node visitor

    Here we visit each node of the abstract tree created by the Scrall parser
    and return data in a format useful for validating a user's action language
    and populating the Shlaer-Mellor metamodel.

    See the scrall.peg file for the formal Scrall grammar.

    The comments for each node visitor includes a more or less recent copy of the
    relevant grammar syntax at the top of each visitor documentation block with
    whitespace elements removed for easy reading.

    When in doubt, consult the scrall.peg file.

    Also consult the wiki in Leon Starr's Scrall repo for a full description of Scrall
    and examples of usage.

    The node and children parameters are rerquired for each visit method and may
    or may not be referenced. Since they are uniform throughout, we do not include
    them in in the comments. See the arpeggio docs for the basics of abstract tree
    visiting.
    """

    @classmethod
    def visit_activity(cls, node, children):
        """
        execution_unit* EOF

        This is the root node. All Scrall language is built up to define a
        single Shlaer-Mellor activity.

        An activity is built up from any number of execution units, including zero.
        It is perfectly okay to define an empty, non-functional activity. This happens
        whenever you define a state, for example, which represents a context, but that does
        not trigger any computation or communication.

        Here we just remove any whitespace and return only the execution units.

        The EOF symbol is a standard terminator at the root level for Arpeggio grammars.
        It signals the parser that there is no more text to parse.
        """
        return [c for c in children if c]

    @classmethod
    def visit_execution_unit(cls, node, children):
        """
        input_tokens? action_group output_tokens? EOL+

        An execution unit is a set of action groups.

        When an action group completes execution it may enable any number of output tokens.
        Each output token represents an outgoing control flow on a data flow diagram.
        Any output token may feed into any number of other action groups in the form of an input token.

        So the syntax defines which input tokens, if any enable this action group to execute and which
        output tokens, if any are enabled upon execution of this action group.

        Every execution unit is terminated by a new line.
        """
        itok = children.results.get('input_tokens')
        otok = children.results.get('output_tokens')
        ag = children.results.get('action_group')[0]
        return Execution_Unit_a(
            input_tokens=None if not itok else itok[0],
            output_tokens=None if not otok else otok[0],
            action_group=ag
        )


    @classmethod
    def visit_block(cls, node, children):
        """
        '{' execution_unit* '}'

        We organize multiple execution units in a block (between brackets) when multiple
        execution units are enabled by the same decision, case, or input tokens.

        This correpsonds to the concept of one or more control flows on a data flow diagram
        enabling multiple processes.
        """
        return Block_a(actions=children)

    @classmethod
    def visit_action(cls, node, children):
        """
        scalar_assignment / delete / scalar_switch / decision / inst_assignment / signal_action / call

        These are (or will be) a complete set of scrall actions. The ordering helps in some cases to prevent
        one type of action from being mistaken for another during the parse. You can't backgrack in a peg
        grammar, so you need to match the pattern right on the first scan.

        There should be only one child element and it will be a named tuple defining the parsed action.
        """
        return children[0]

    # Control flow tokens
    @classmethod
    def visit_input_tokens(cls, node, children):
        """
        sequence_token+
        """
        return children

    @classmethod
    def visit_output_tokens(cls, node, children):
        """
        sequence_token+
        """
        return children

    @classmethod
    def visit_sequence_token(cls, node, children):
        """
        '<' token_name '>'

         Named control flow
        """
        return Sequence_Token_a(name=children[0])

    @classmethod
    def visit_token_name(cls, node, children):
        """
        r'[A-Za-z0-9_]+'
        No spaces in token names, often single digit: <1>

        Since this is a terminal, we need to grab the name from the node.value
        """
        return node.value

    # Created and delete actions
    @classmethod
    def visit_delete(cls, node, children):
        """
        '!*' instance_set

        """
        iset = children.results.get('instance_set')
        return Delete_Action_a(instance_set=iset)

    # Decision and switch actions
    @classmethod
    def visit_decision(cls, node, children):
        """
        scalar_expr true_result false_result?

        Control flow version of an if-then
        """
        return Decision_a(input=children[0], true_result=children[1], false_result=None if len(children) < 3 else children[2])

    @classmethod
    def visit_true_result(cls, node, children):
        """
        DECISION_OP action_group

        Actions to be executed when the decision evaluates to true
        """
        return children[0]

    @classmethod
    def visit_false_result(cls, node, children):
        """
        FALSE_RESULT_OP action_group

        Actions to be executed when the decision evaluates to false
        """
        return children[0]

    @classmethod
    def visit_scalar_switch(cls, node, children):
        """
        scalar_expr DECISION_OP case_block

        Boolean expr triggers case_block
        """
        return Scalar_Switch_a(
            scalar_input_flow=children.results['scalar_expr'],
            cases=children.results['case_block'][0]
        )

    @classmethod
    def visit_case_block(cls, node, children):
        """
        '{' case+ '}'

        One or more cases between brackets
        """
        return children

    @classmethod
    def visit_case(cls, node, children):
        """
        enum_value+ ':' execution_unit

        One or more enumerated values that triggers an execution unit
        """
        return Case_a(
            enums=children.results['enum_value'],
            execution_unit=children.results['execution_unit'][0]
        )

    @classmethod
    def visit_enum_value(cls, node, children):
        """
        '.' name
        """
        return children.results['name'][0]

    # Signal action
    @classmethod
    def visit_signal_action(cls, node, children):
        """
        Returns event_name ?supplied_params instance_set
        """
        s = children.results['signal'][0]
        delay = children.results.get('delay')
        return Signal_Action_a(event=s.event, supplied_params=s.supplied_params, dest=s.dest, delay=delay)

    @classmethod
    def visit_signal(cls, node, children):
        """
        name supplied_params? SIGNAL_OP instance_set

        An event name, any supplied parameters, the '->' signal symbol and a target
        instance set
        """
        params = children.results.get('supplied_params', [])
        return Signal_a(
            event=children.results['name'],
            supplied_params=params,
            dest=children.results.get('instance_set')
        )

    @classmethod
    def visit_delay(cls, node, children):
        """
        DELAY_OP scalar_expr

        A time or time interval
        """
        return children[0]

    # Instance set assignment and selection
    @classmethod
    def visit_inst_assignment(cls, node, children):
        """
        name INST_ASSIGN instance_set
        """
        return Inst_Assignment_a(
            lhs=children.results['name'][0],
            card='1' if children.results['INST_ASSIGN'] == '.=' else 'Mc',
            rhs=children.results['instance_set']
        )

    @classmethod
    def visit_instance_set(cls, node, children):
        """
        (name / path) (selection / operation / path)*

        An instance set begins with a required name (instance flow) or a path. The path can then be followed
        by any sequence of selection, operation, and paths. The parser won't find two paths in sequence since
        any encounter path will be fully consumed
        """
        return INST_a(children)

    @classmethod
    def visit_selection(cls, node, children):
        """
        '(' select_phrase ')'
        """
        return Selection_a(card=children[0][0], criteria=None if len(children[0]) < 2 else children[0][1])

    @classmethod
    def visit_select_phrase(cls, node, children):
        """
        (CARD ',' criteria) / CARD / criteria

        """
        explicit_card = children.results.get('CARD')
        card = '*' if not explicit_card else explicit_card[0]
        criteria = children.results.get('scalar_expr')
        if criteria:
            return [card, criteria[0]]
        else:
            return [card]

    # Scalar assignment and operations
    @classmethod
    def visit_scalar_assignment(cls, node, children):
        """
        name SCALAR_ASSIGN scalar_expr
        """
        return Scalar_Assignment_a(*children)

    @classmethod
    def visit_scalar_expr(cls, node, children):
        """
        Returns a fully parsed scalar expression
        """
        return children[0]

    @classmethod
    def visit_scalar_logical_or(cls, node, children):
        """
        scalar_logical_and (OR scalar_logical_and)*

        Returns a higher precedence operation or one or more OR'ed conjunctions
        """
        if len(children) == 1: # No OR operation
            return children[0]
        else:
            return BOOL_a('OR', children.results['scalar_logical_and'])

    @classmethod
    def visit_scalar_logical_and(cls, node, children):
        """
        equality (AND equality)*

        Returns a higher precedence operation or one or more AND'ed equalities
        """
        if len(children) == 1: # No AND operation
            return children[0]
        else:
            return BOOL_a('AND', children.results['equality'])

    @classmethod
    def visit_comparison(cls, node, children):
        """
        comparison = addition (COMPARE addition)*

        Returns a higher precedence operation or one or more compared additions (>, <=, etc)
        """
        if len(children) == 1:
            return children[0]
        else:
            return BOOL_a(children.results['COMPARE'], children.results['addition'])

    @classmethod
    def visit_addition(cls, node, children):
        """
        factor (ADD factor)*

        Returns a higher precedence operation or one or more added/subtracted factors
        """
        if len(children) == 1:
            return children[0]
        else:
            return MATH_a(children.results['ADD'], children.results['factor'])

    @classmethod
    def visit_equality(cls, node, children) -> BOOL_a:
        """
        comparison (EQUAL comparison)*

        Returns a higher precedence operation or one or more equalities (==, !=)
        """
        if len(children) == 1:
            return children[0]
        else:
            # Convert ':' to '==' if found
            eq_map = ['==' if e in ('==',':') else '!=' for e in children.results['EQUAL']]
            return BOOL_a(eq_map, children.results['comparison'])

    @classmethod
    def visit_factor(cls, node, children):
        """
        term (MULT term)*

        Returns a higher precedence operation or one or more multipled/divided terms
        """
        if len(children) == 1:
            return children[0]
        else:
            return MATH_a(children.results['MULT'], children.results['term'])

    @classmethod
    def visit_term(cls, node, children):
        """
        NOT? UNARY_MINUS? (scalar / scalar_expr)
        ---
        If the not or unary minus operations are not specified, returns whatever was parsed out earlier,
        either a simple scalar (attribute, attribute access, etc) or any scalar expression

        Otherwise, a unary minus expression nested inside a boolean not operation, or just the boolean not,
        or just the unary minus expressions individually are returned.
        """
        s = children.results.get('scalar')
        s = s if s else children.results['scalar_expr']
        scalar = s[0]
        if len(children) == 1:
            return scalar
        not_op = children.results.get('NOT')
        unary_minus = children.results.get('UNARY_MINUS')
        if unary_minus and not not_op:
            return UNARY_a('-', scalar)
        if not_op and not unary_minus:
            return BOOL_a('NOT', scalar)
        if unary_minus and not_op:
            return BOOL_a('NOT', UNARY_a('-', scalar))


    # Synchronous method or operation

    @classmethod
    def visit_call(cls, node, children):
        """
        instance_set
        Post-parse verify that last element is an operation, otherwise invalid call
        """
        if not isinstance(children[-1], Op_a):
            # There's no terminating operation in the action, so this isn't a complete call
            _logger.error(f"Call action without operation: [{children.results}]")
            raise ScrallCallWithoutOperation(children.results)
        return Call_a(subject=children[0], ops=children[1:])

    @classmethod
    def visit_operation(cls, node, children):
        """
        Children are name, ?supplied_params
        Returns op_name ?supplied_params dest
        """
        op_name = children[0]
        params = [] if len(children) == 1 else children[-1]
        return Op_a(op_name=op_name, supplied_params=params)

    @classmethod
    def visit_param(cls, node, children):
        """
        (name ':')? scalar_expr

        If only a scalar_expr is present, it means that the supplied expr has the same name
        Ex: ( shaft id ) as that of the required parameter. Short for ( shaft id : shaft id ). This
        is a convenience that elminates the need for name doubling in a supplied parameter set
        """
        s = children.results['scalar_expr'][0]
        p = children.results.get('name')
        if not p and not isinstance(s,str):
            _logger.error(f"Paramenter name not supplied with expression value: [{children.results}]")
            raise ScrallMissingParameterName(children.results)
        return Supplied_Parameter_a(pname=s if not p else p[0], sval=s)

    @classmethod
    def visit_supplied_params(cls, node, children):
        """
        '(' (param (',' param)*)? ')'

        Could be () or a list of multiple parameters

        """
        return children if children else None


    def visit_attr_access(self, node, children):
        return Attr_Access_a(cname=children[0], attr=children[1])

    # Relationship traversal (paths)
    @classmethod
    def visit_path(cls, node, children):
        """ hop+  A sequence of hops """
        return PATH_a(children)

    @classmethod
    def visit_hop(cls, node, children):
        """ '/' (rnum / name)  An rnum, phrase, or class name """
        return children[0]

    # Names
    @classmethod
    def visit_rnum(cls, node, children):
        """
        r'O?R[1-9][0-9]*'
        Relationship number such as R23

        This is how relationships are named
        """
        return R_a(node.value)

    @classmethod
    def visit_name(cls, node, children):
        """ Join words and delimiters """
        return ''.join(children)

    # Discarded whitespace and comments
    @classmethod
    def visit_LINEWRAP(cls, node, children):
        """
        EOL SP*
        end of line followed by optional indent on next line
        """
        return None

    @classmethod
    def visit_EOL(cls, node, children):
        """
        SP* COMMENT? '\n'

        end of line: Spaces, Comments, blank lines, whitespace we can omit from the parser result
        """
        return None

    @classmethod
    def visit_SP(cls, node, children):
        """ ' '  Single space character (SP) """
        return None