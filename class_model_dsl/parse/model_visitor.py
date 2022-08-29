""" model_visitor.py """

from arpeggio import PTNodeVisitor

class MetadataVisitor(PTNodeVisitor):

    # Elements
    def visit_nl(self, node, children):
        return None

    def visit_sp(self, node, children):
        return None

    # Comments
    # def visit_ig_line(self, node, children):
    #     print("Ignoring line")
    #     return None


    # def visit_comment(self, node, children):
    #     return None

    # Metadata
    def visit_text_item(self, node, children):
        return children[0], False  # Item, Not a resource

    def visit_resource_item(self, node, children):
        return ''.join(children), True  # Item, Is a resource

    def visit_item_name(self, node, children):
        return ''.join(children)

    def visit_data_item(self, node, children):
        return { children[0]: children[1] }

    # Root
    def visit_metadata(self, node, children):
        """Meta data section"""
        print("check")
        items = {k: v for c in children for k, v in c.items()}
        return items

