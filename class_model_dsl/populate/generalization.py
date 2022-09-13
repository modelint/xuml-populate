"""
generalization.py – Convert parsed relationship to a relation
"""

import logging
from class_model_dsl.mp_exceptions import LessThanTwoSubclassesInGeneralization


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

        # Populate
        self.logger.info(f"Populating Generalization [{self.relationship.rnum}]")
        self.relationship.domain.model.Insert('Generalization', [
            self.relationship.rnum, self.relationship.domain.name, self.superclass])
        # Superclass
        self.relationship.domain.model.Insert('Facet', [
            self.relationship.rnum, self.superclass, self.relationship.domain.name])
        self.relationship.domain.model.Insert('Superclass', [
            self.relationship.rnum, self.superclass, self.relationship.domain.name])
        for subclass in self.subclasses:
            self.relationship.domain.model.Insert('Facet', [
                self.relationship.rnum, subclass, self.relationship.domain.name])
            self.relationship.domain.model.Insert('Subclass', [
                self.relationship.rnum, subclass, self.relationship.domain.name])
        if len(self.subclasses) < 2:
            self.logger.error(f"Less than two subclasses in [{self.relationship.rnum}].")
            raise LessThanTwoSubclassesInGeneralization(rnum=self.relationship.rnum)
        self.relationship.domain.model.Insert('Minimal Partition', [
            self.relationship.rnum, self.relationship.domain.name, self.subclasses[0], self.subclasses[1]])

        # Attribute References
        # If abbreviated, expand <subclass> abbreviation one explcit reference per subclass
        if len(self.genrefs) == 1 and self.genrefs[0]['source']['class'] == '<subclass>':
            self.genrefs = [{'source': {'class': s, 'attrs': self.genrefs[0]['source']['attrs']},
                             'target': self.genrefs[0]['target']} for s in self.subclasses]

        for ref in self.genrefs:
            self.relationship.domain.model.Insert('Reference',
                                                  ['G', ref['source']['class'], ref['target']['class'],
                                                   self.relationship.rnum,
                                                   self.relationship.domain.name])
            self.relationship.domain.model.Insert('Generalization Reference',
                                                  [ref['source']['class'], ref['target']['class'],
                                                   self.relationship.rnum,
                                                   self.relationship.domain.name])
            self.relationship.domain.model.Insert('Formalizing Class Role',
                                                  [self.relationship.rnum, ref['source']['class'],
                                                                           self.relationship.domain.name])
            # Create attribute references for each subclass -> superclass reference
            for from_attr, to_attr in zip(ref['source']['attrs'], ref['target']['attrs']):
                self.relationship.domain.model.Insert('Attribute Reference', [from_attr, ref['source']['class'], to_attr,
                                                                 ref['target']['class'], self.relationship.domain.name,
                                                                 self.relationship.rnum, 'G', ref['id']])