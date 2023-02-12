""" scrall_visitor.py """
from arpeggio import PTNodeVisitor

class ScrallVisitor(PTNodeVisitor):

    def visit_statement(self, node, children):
        return children

    def visit_activity(self, node, children):
        return children