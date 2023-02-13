""" scrall_visitor.py """
from arpeggio import PTNodeVisitor
from collections import namedtuple

Signal_a = namedtuple('Signal_a', 'event_name path')

class ScrallVisitor(PTNodeVisitor):

    def visit_activity(self, node, children):
        return [c for c in children if c]

    def visit_action(self, node, children):
        return children

    def visit_signal_action(self, node, children):
        return Signal_a(event_name=children[0]['name'], path=children[1]['path'])

    def visit_path(self, node, children):
        return {'path': children}

    def visit_hop(self, node, children):
        return children[0]

    def visit_rnum(self, node, children):
        """ Join words and delimiters """
        return {'rnum': node.value}

    def visit_name(self, node, children):
        """ Join words and delimiters """
        return {'name': ''.join(children)}

    def visit_SP(self, node, children):
        """ Discard space character """
        return None

    def visit_nl(self, node, children):
        """ Discard comments and blank lines """
        return None


