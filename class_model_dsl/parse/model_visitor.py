""" model_visitor.py """

from arpeggio import PTNodeVisitor

class SubsystemVisitor(PTNodeVisitor):

    # Root
    def visit_subsystem(self, node, children):
        """All classes and relationships in the subsystem"""
        return children

    # Metadata
    def visit_metadata(self, node, children):
        """Meta data section"""
        print("check")
        items = {k: v for c in children for k, v in c.items()}
        return items

    def visit_text_item(self, node, children):
        return children[0], False  # Item, Not a resource

    def visit_resource_item(self, node, children):
        return ''.join(children), True  # Item, Is a resource

    def visit_item_name(self, node, children):
        return ''.join(children)

    def visit_data_item(self, node, children):
        return { children[0]: children[1] }

    # Classes
    def visit_class_set(self, node, children):
        """All of the classes"""
        return children

    def visit_class_block(self, node, children):
        """A complete class with attributes, methods, state model"""
        # TODO: No state models yet
        class_attrs = children[0] | children[1]
        block = class_attrs if len(children) == 2 else class_attrs | children[2]
        return block

    def visit_attr_block(self, node, children):
        """Attribute text (unparsed)"""
        # TODO: Parse these eventually
        return {"attributes": children}

    # Elements
    def visit_nl(self, node, children):
        return None

    def visit_sp(self, node, children):
        return None
