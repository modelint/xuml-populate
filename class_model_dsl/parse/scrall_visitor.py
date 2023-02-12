""" scrall_visitor.py """
from arpeggio import PTNodeVisitor

class ScrallVisitor(PTNodeVisitor):

    def visit_activity(self, node, children):
        return children

    def visit_statement(self, node, children):
        return children

    def visit_name(self, node, children):
        return ''.join(children)

    def visit_word(self, node, children):
        return node.value

    def visit_comment(self, node, children):
        return children


