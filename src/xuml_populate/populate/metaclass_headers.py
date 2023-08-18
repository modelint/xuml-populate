"""
metaclass_headers.py – A relation header for each metaclass (minus the types)
"""

# Table header attributes for each metamodel class
# This is used when inserting a tuple into a metammodel relvar

header = {
    'Attribute': ('Name', 'Class', 'Domain', ),
    'Class': ('Name', 'Domain', ),
    'Domain': ('Name', ),
    'Identifier': ('Number', 'Class', 'Domain', ),
    'Identifier Attribute': ('Identifier', 'Attribute', 'Class', 'Domain', ),
}