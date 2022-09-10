"""
attribute_reference.py – Create an attribute reference
"""
import logging


class AttributeReference:
    """
    Build all attribute references for a relationship
    """

    def __init__(self, relationship, classes):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.relationship = relationship
        self.classes = classes
