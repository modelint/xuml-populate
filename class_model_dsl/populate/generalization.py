"""
generalization.py – Convert parsed relationship to a relation
"""

import logging

class Generalization:
    """
    Create a generalization relationship relation
    """

    def __init__(self, relationship):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.relationship = relationship

        self.subclasses = relationship.parse_data['subclasses']
        self.superclass = relationship.parse_data['superclass']
        self.genrefs = relationship.parse_data['genrefs']

        self.relationship.domain.model.Insert('Generalization', [self.relationship.rnum, self.relationship.domain.name])

        print()
        # Attribute References
        for from_attr, to_attr in zip(self.ref2_source['attrs'], self.ref2_target['attrs']):
            self.domain.model.Insert('Attribute Reference', [from_attr, self.ref2_source['class'], to_attr,
                                                             self.ref2_target['class'], self.domain.name,
                                                             self.rnum, 'P', self.ref1['id']])
        print()