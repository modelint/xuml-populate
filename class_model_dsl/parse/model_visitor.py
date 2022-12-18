""" model_visitor.py """

from arpeggio import PTNodeVisitor
from collections import namedtuple

ID = namedtuple('_ID', 'number superid')

class SubsystemVisitor(PTNodeVisitor):

    # Root
    def visit_subsystem(self, node, children):
        """All classes and relationships in the subsystem"""
        return children

    # Metadata
    def visit_metadata(self, node, children):
        """Meta data section"""
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

    # Domain
    def visit_domain_header(self, node, children):
        """Domain name and optional alias"""
        items = {k: v for d in children for k, v in d.items()}
        return items

    def visit_domain_name(self, node, children):
        name = ''.join(children)
        return {'name': name }

    def visit_domain_alias(self, node, children):
        """Alias of domain"""
        return { 'alias': children[0] }

    # Subsystem
    def visit_subsystem_header(self, node, children):
        """Subsystem name, numbering range, and optional alias"""
        items = {k: v for d in children for k, v in d.items()}
        return items

    def visit_subsystem_name(self, node, children):
        name = ''.join(children)
        return {'name': name }

    def visit_subsystem_alias(self, node, children):
        """Alias of domain"""
        return { 'alias': children[0] }

    def visit_num_range(self, node, children):
        """Subsystem numbering range"""
        return { 'range': (int(children[0]), int(children[1])) }

    # Classes
    def visit_class_set(self, node, children):
        """All of the classes"""
        return children

    def visit_class_block(self, node, children):
        """A complete class with attributes, methods, state model"""
        class_attrs = children[0] | children[1]
        block = class_attrs if len(children) == 2 else class_attrs | children[2]
        return block

    def visit_class_name(self, node, children):
        name = ''.join(children)
        return {'name': name }

    def visit_class_alias(self, node, children):
        """Abbreviated class_alias name of class"""
        return { 'alias': children[0] }

    def visit_import(self, node, children):
        """Imported class marker"""
        d = {'import': children[0]}
        return d

    def visit_class_header(self, node, children):
        """Beginning of class section, includes name, optional class_alias and optional import marker"""
        items = {k: v for d in children for k, v in d.items()}
        return items

    # Attributes
    def visit_attr_block(self, node, children):
        """Attribute text (unparsed)"""
        return {"attributes": children}

    def visit_attribute(self, node, children):
        """An attribute with its tags and optional explicit type"""
        items = {k: v for d in children for k, v in d.items()}
        return items

    def visit_attr_name(self, node, children):
        name = ''.join(children)
        return {'name': name }

    def visit_type_name(self, node, children):
        name = ''.join(children)
        return {'type': name }

    def visit_attr_tags(self, node, children):
        """Tag values organized in a list by tag"""
        tdict = {}  # Tag dictionary of value lists per tag
        for tag in ['I', 'R']:  # Identifier and referential attr tags
            tdict[tag] = [c[tag] for c in children if tag in c]  # Create list of values per tag from children
        return tdict

    def visit_attr_tag(self, node, children):
        """Beginning of class section, includes name, optional alias and optional import marker"""
        item = children[0]
        return item

    def visit_rtag(self, node, children):
        """
        Referential attribute tag

        Here we expect examples like these:
            R21c
            R22
            OR23

        The trick is to extract the number, conditionality status, and either R or OR
        """
        # 'R' gets swallowed by the parser since it is a literal, but 'O' shows up as a child
        # element for some reason. Not sure why 'O' is treated differently, but this complicates
        # the code below. Best solution is to clean up the grammar eventually.

        tag = 'OR' if node[0].value == 'O' else 'R'
        rnum_index = 1 if tag == 'OR' else 0
        rnum = int(rnum_index)
        constraint = children[-1] == 'c'
        rtag = {tag: (rnum, constraint) }
        return rtag

    def visit_itag(self, node, children):
        """Identifier attribute tag"""
        itag = None
        if not children:
            itag = ID(1, False)
        else:
            super = True if children[0] == '*' else False
            tag_num = children[0] if not super else children[1]
            itag = ID(int(tag_num), super)
        id = {'I': itag }
        return id

    # Relationships
    # ---
    def visit_rel_section(self, node, children):
        """Relationships section with all of the relationships"""
        return children

    def visit_rel(self, node, children):
        """Relationship rnum and rel data"""
        return {**children[0], **children[1]}

    def visit_rname(self, node, children):
        """The Rnum on any relationship"""
        return {"rnum": children[0]}

    # Ordinal relationship
    def visit_ordinal_rel (self, node, children):
        """Ordinal relationship """
        items = {k: v for d in children for k, v in d.items()}
        return items

    def visit_ascend(self, node, children):
        """Ascend-descend phrases"""
        items = {node.rule_name: {"highval": children[0], "lowval": children[1], "cname": children[2]['name']}}
        return items

    def visit_highval(self, node, children):
        """High value phrase"""
        return ''.join(children)

    def visit_lowval(self, node, children):
        """Low value phrase"""
        return ''.join(children)

    def visit_oform(self, node, children):
        """Ordinal formalization"""
        items = {node.rule_name: {"ranking attr": children[0], "id": children[1]['I'].number}}
        return items

    # Binary association
    def visit_binary_rel(self, node, children):
        """Binary relationship with or without an association class"""
        items = {k: v for d in children for k, v in d.items()}
        return items

    def visit_t_side(self, node, children):
        """T side of a binary association"""
        items = {node.rule_name: {"phrase": children[0], "mult": children[1], "cname": children[2]}}
        return items

    def visit_p_side(self, node, children):
        """P side of a binary association"""
        items = {node.rule_name: {"phrase": children[0], "mult": children[1], "cname": children[2]}}
        return items

    def visit_phrase(self, node, children):
        """Phrase on one side of a binary relationship phrase"""
        phrase = ''.join(children)
        return phrase

    def visit_mult(self, node, children):
        """Binary association (not association class) multiplicity"""
        mult = node.value  # No children because literal 1 or M is thrown out
        return mult

    def visit_assoc_class(self, node, children):
        """Association class name and multiplicity"""
        items = { "assoc_mult": children[0], "assoc_cname": children[1] }
        return items

    def visit_binref(self, node, children):
        """Single class to single class ref"""
        id = 1 if len(children) < 3 else children[2]['I']  # referenced model identifier, default is I1
        ref = {'source': children[0], 'target': children[1], 'id': id}
        return ref

    def visit_ref1(self, node, children):
        """Either a simple or t or p reference (t or p if associative)"""
        id = 1 if len(children) < 3 else children[2]['I']  # referenced model identifier, default is I1
        ref = { 'ref1': {'source': children[0], 'target': children[1], 'id': id}}
        return ref

    def visit_ref2(self, node, children):
        """Either a t or p reference, requires an association class"""
        id = 1 if len(children) < 3 else children[2]['I']  # referenced model identifier, default is I1
        ref = { 'ref2': {'source': children[0], 'target': children[1], 'id': id}}
        return ref

    # Generalization
    def visit_gen_rel(self, node, children):
        """Generalization relationship"""
        items = {k: v for d in children[1:] for k, v in d.items()}
        items["superclass"] = children[0]
        return items

    def visit_superclass(self, node, children):
        """Superclass in a generalization relationship"""
        return children[0]

    def visit_subclasses(self, node, children):
        """Subclass in a generalization relationship"""
        return { 'subclasses': children }

    def visit_subclass(self, node, children):
        """Subclass in a generalization relationship"""
        return children[0]

    def visit_genref(self, node, children):
        """Either abbreviated <subclass> source or explicit source for each subclass"""
        genrefs = {'genrefs': children}
        return genrefs

    def visit_single_line_genref(self, node, children):
        """Either a t or p reference, requires an association class"""
        id = 1 if len(children) < 3 else children[2]['I']  # referenced model identifier, default is I1
        grefs = {'source': children[0], 'target': children[1], 'id': id}
        return grefs


    def visit_source_attrs(self, node, children):
        """Source attributes referring to target attributes"""
        class_name = children[0]['name']
        attrs = children[1]
        items = {'class': class_name, 'attrs': attrs}
        return items

    def visit_target_attrs(self, node, children):
        """Referenced target attributes"""
        class_name = children[0]['name']
        attrs = children[1]
        items = {'class': class_name, 'attrs':attrs}
        return items

    def visit_allsubs_attrs(self, node, children):
        """A subset of attrs from a single class"""
        items = { 'class': '<subclass>', 'attrs': children[0]}
        return items

    def visit_single_class_attrs(self, node, children):
        """A subset of attrs from a single class"""
        items = { 'class': children[0], 'attrs': children[1]}
        return items

    def visit_attr_set(self, node, children):
        """Source attributes referring to some target"""
        attrs = [c['name'] for c in children]
        return attrs

    #---

    # Text and delimiters
    def visit_acword(self, node, children):
        """All caps word"""
        return node.value  # No children since this is a literal

    def visit_icaps_name(self, node, children):
        """Model element name"""
        name = ''.join(children)
        return name

    def visit_nl(self, node, children):
        return None

    def visit_sp(self, node, children):
        return None
