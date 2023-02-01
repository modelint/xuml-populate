""" statemodel_visitor.py """

from arpeggio import PTNodeVisitor
from collections import namedtuple

# These named tuples help package up parsed data into meaningful chunks of state model content
# To avoid a collision with any application tuple names, we append _p to indicate parser output
StateBlock_p = namedtuple('StateBlock_p', 'state activity transitions')
"""Parsed model data describing a state including its activity, optional creation event and optional exit transitions"""
Parameter_p = namedtuple('Parameter_p', 'name type')
"""Parsed name and data type of a parameter in a state model event signature"""
StateSpec_p = namedtuple('StateSpec_p', 'name deletion signature')
"""Parsed name of a real state, its type (deletion or non deletion) and state signature"""
Transition_p = namedtuple('Transition_p', 'event to_state')
"""Parsed transition with event and destination state"""


class StateModelVisitor(PTNodeVisitor):
    """Visit parsed units of an Executable UML State Model"""
    # Each header comment below corresponds to section in statemodel.peg file

    # Elements
    def visit_nl(self, node, children):
        """New line character"""
        return None

    def visit_sp(self, node, children):
        """Single space character"""
        return None

    def visit_name(self, node, children):
        """Model element name"""
        name = ''.join(children)
        return name

    def visit_body_line(self, node, children):
        """Lines that we don't need to parse yet, but eventually will"""
        # TODO: These should be attributes and actions
        body_text_line = children[0]
        return body_text_line

    # State block
    def visit_state_name(self, node, children):
        """Model element name"""
        name = ''.join(children)
        return name

    def visit_creation(self, node, children):
        return 'creation'

    def visit_deletion(self, node, children):
        return 'deletion'

    def visit_parameter_name(self, node, children):
        """Model element name"""
        name = ''.join(children)
        return name

    def visit_type_name(self, node, children):
        """All characters composing a data type name"""
        name = ''.join(children)
        return name

    def visit_parameter(self, node, children):
        """param_name type_name"""
        return Parameter_p(name=children[0], type=children[1])

    def visit_parameter_set(self, node, children):
        """list of { param_name: type_name } pairs"""
        return children

    def visit_signature(self, node, children):
        """Strips out parentheses"""
        return children[0]

    def visit_state_header(self, node, children):
        """
        There are four possible cases:
            state name
            state name (deletion)
            state name (signature)
            state name (signature) (deletion)
        """
        n = children[0]  # State name
        clen = len(children)
        deletion = True if clen > 1 and 'deletion' in children else False
        sig = []
        if deletion and clen == 3 or not deletion and clen == 2:
            sig = children[1]
        return StateSpec_p(name=n, deletion=deletion, signature=sig)

    def visit_transition(self, node, children):
        """event destination_state"""
        return Transition_p(event=children[0], to_state=None if len(children) < 2 else children[1])

    def visit_transitions(self, node, children):
        """All transitions exiting a state including any creation transitions"""
        return children

    def visit_activity(self, node, children):
        """Required state activity, which may or may not contain any actions"""
        return children

    def visit_state_block(self, node, children):
        """All state data"""
        s = children[0]  # State info
        a = children[1]  # Activity (could be empty, but always provided)
        t = [] if len(children) < 3 else children[2]  # Optional transitions
        sblock = StateBlock_p(state=s, activity=a, transitions=t)
        return sblock

    # Initial transitions
    def visit_initial_transitions(self, node, children):
        return children

    # Events
    def visit_event_name(self, node, children):
        """Model element name"""
        name = ''.join(children)
        return name

    def visit_event_spec(self, node, children):
        """event_name"""
        return children[0]

    def visit_events(self, node, children):
        """A list of event names"""
        return list(children)

    # Scope
    def visit_assigner(self, node, children):
        """Scope: If value supplied this is an assigner state model"""
        return {'rel': children[0] }

    def visit_lifecycle(self, node, children):
        """Scope: If value supplied this is a lifecycle state model"""
        return {'class': children[0] }

    def visit_domain_header(self, node, children):
        """domain_name"""
        name = children[0]
        return name

    # Metadata
    def visit_text_item(self, node, children):
        return children[0], False  # Item, Not a resource

    def visit_resource_item(self, node, children):
        return ''.join(children), True  # Item, Is a resource

    def visit_item_name(self, node, children):
        return ''.join(children)

    def visit_data_item(self, node, children):
        return { children[0]: children[1] }

    def visit_metadata(self, node, children):
        """Meta data section"""
        items = {k: v for c in children for k, v in c.items()}
        return items

    # Root
    def visit_statemodel(self, node, children):
        """The complete state machine (state model)"""
        return children
