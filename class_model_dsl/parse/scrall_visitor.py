""" scrall_visitor.py """
from arpeggio import PTNodeVisitor
from collections import namedtuple

Signal_a = namedtuple('Signal_a', 'event_name destination')

class ScrallVisitor(PTNodeVisitor):

    def visit_activity(self, node, children):
        return [c for c in children if c]

    def visit_action(self, node, children):
        return children

    def visit_signal_action(self, node, children):
        return Signal_a(event_name=children[0], destination=children[1]['destination'])
        return children

    def visit_destination(self, node, children):
        return {'destination': children[0]}

    def visit_name(self, node, children):
        """ Join words and delimiters """
        return ''.join(children)

    def visit_nl(self, node, children):
        """ Discard comments and blank lines """
        return None


