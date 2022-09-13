"""
binary_association.py – Convert parsed relationship to a relation
"""

import logging


class BinaryAssociation:
    """
    Create a binary association relation
    """

    def __init__(self, relationship):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.relationship = relationship

        self.t_side = relationship.parse_data.get('t_side')
        self.p_side = relationship.parse_data.get('p_side')
        self.ref1 = relationship.parse_data.get('ref1')
        self.ref1_source = None if not self.ref1 else self.ref1['source']
        self.ref1_target = None if not self.ref1 else self.ref1['target']
        self.ref2 = relationship.parse_data.get('ref2')  # Supplied only for an associative binary
        self.ref2_source = None if not self.ref2 else self.ref2['source']
        self.ref2_target = None if not self.ref2 else self.ref2['target']
        self.assoc_cname = relationship.parse_data.get('assoc_cname')
        self.assoc_mult = relationship.parse_data.get('assoc_mult')

        # Populate
        self.logger.info(f"Populating Binary Association [{self.relationship.rnum}]")
        self.relationship.domain.model.Insert('Association', [self.relationship.rnum, self.relationship.domain.name])
        self.relationship.domain.model.Insert('Binary Association',
                                              [self.relationship.rnum, self.relationship.domain.name])
        if self.assoc_cname:
            self.relationship.domain.model.Insert('Association Class', [self.relationship.rnum, self.assoc_cname,
                                                                        self.relationship.domain.name])

        # Populate the T and P perspectives of an asymmetric binary association
        self.relationship.domain.model.Insert('Perspective',
                                              ['T', self.relationship.rnum, self.relationship.domain.name,
                                               self.t_side['cname'], self.t_side['phrase'],
                                               True if 'c' in self.t_side['mult'] else False, self.t_side['mult'][0]]
                                              )
        self.relationship.domain.model.Insert('Asymmetric Perspective',
                                              ['T', self.relationship.rnum, self.relationship.domain.name])
        self.relationship.domain.model.Insert('T Perspective', [self.relationship.rnum, self.relationship.domain.name])

        self.relationship.domain.model.Insert('Perspective',
                                              ['P', self.relationship.rnum, self.relationship.domain.name,
                                               self.p_side['cname'], self.p_side['phrase'],
                                               True if 'c' in self.p_side['mult'] else False, self.p_side['mult'][0]]
                                              )
        self.relationship.domain.model.Insert('Asymmetric Perspective',
                                              ['P', self.relationship.rnum, self.relationship.domain.name])
        self.relationship.domain.model.Insert('P Perspective', [self.relationship.rnum, self.relationship.domain.name])

        # Create reference
        if not self.ref2:  # Simple binary association
            self.relationship.domain.model.Insert('Reference',
                                                  ['R', self.ref1_source['class'], self.ref1_source['class'],
                                                   self.relationship.rnum,
                                                   self.relationship.domain.name])
            referenced_perspective = 'T' if self.ref1_target['class'] == self.t_side['cname'] else 'P'
            self.relationship.domain.model.Insert('Association Reference',
                                                  ['R', self.ref1_source['class'], self.ref1_target['class'],
                                                   self.relationship.rnum,
                                                   self.relationship.domain.name,
                                                   referenced_perspective])
            self.relationship.domain.model.Insert('Simple Association Reference',
                                                  [self.ref1_source['class'], self.ref1_target['class'],
                                                   self.relationship.rnum,
                                                   self.relationship.domain.name])
            self.relationship.domain.model.Insert('Referring Class', [self.relationship.rnum, self.ref1_source['class'],
                                                                      self.relationship.domain.name])
            self.relationship.domain.model.Insert('Formalizing Class Role',
                                                  [self.relationship.rnum, self.ref1_source['class'],
                                                   self.relationship.domain.name])

            # Simple Attribute Reference
            for from_attr, to_attr in zip(self.ref1_source['attrs'], self.ref1_target['attrs']):
                self.relationship.domain.model.Insert('Attribute Reference',
                                                      [from_attr, self.ref1_source['class'], to_attr,
                                                       self.ref1_target['class'], self.relationship.domain.name,
                                                       self.relationship.rnum, 'R', self.ref1['id']])
        else:  # Binary associative (with association class)
            # T Reference
            self.relationship.domain.model.Insert('Reference',
                                                  ['T', self.ref1_source['class'], self.ref1_target['class'],
                                                   self.relationship.rnum,
                                                   self.relationship.domain.name])
            self.relationship.domain.model.Insert('Formalizing Class Role', [self.relationship.rnum, self.assoc_cname,
                                                                             self.relationship.domain.name])

            self.relationship.domain.model.Insert('Association Reference',
                                                  ['T', self.ref1_source['class'], self.ref1_target['class'],
                                                   self.relationship.rnum,
                                                   self.relationship.domain.name,
                                                   'T'])
            self.relationship.domain.model.Insert('Association Class Reference',
                                                  ['T', self.ref1_source['class'], self.ref1_target['class'],
                                                   self.relationship.rnum,
                                                   self.relationship.domain.name])
            self.relationship.domain.model.Insert('T Reference',
                                                  [self.ref1_source['class'], self.ref1_target['class'],
                                                   self.relationship.rnum,
                                                   self.relationship.domain.name])
            # T Attribute References
            for from_attr, to_attr in zip(self.ref1_source['attrs'], self.ref1_target['attrs']):
                self.relationship.domain.model.Insert('Attribute Reference',
                                                      [from_attr, self.ref1_source['class'], to_attr,
                                                       self.ref1_target['class'], self.relationship.domain.name,
                                                       self.relationship.rnum, 'T', self.ref1['id']])

            # P Reference
            self.relationship.domain.model.Insert('Reference',
                                                  ['P', self.ref2_source['class'], self.ref2_target['class'],
                                                   self.relationship.rnum,
                                                   self.relationship.domain.name])
            self.relationship.domain.model.Insert('Association Reference',
                                                  ['P', self.ref2_source['class'], self.ref2_target['class'],
                                                   self.relationship.rnum,
                                                   self.relationship.domain.name,
                                                   'P'])
            self.relationship.domain.model.Insert('Association Class Reference',
                                                  ['P', self.ref2_source['class'], self.ref2_target['class'],
                                                   self.relationship.rnum,
                                                   self.relationship.domain.name])
            self.relationship.domain.model.Insert('P Reference',
                                                  [self.ref2_source['class'], self.ref1_target['class'],
                                                   self.relationship.rnum,
                                                   self.relationship.domain.name])

            # P Attribute References
            for from_attr, to_attr in zip(self.ref2_source['attrs'], self.ref2_target['attrs']):
                self.relationship.domain.model.Insert('Attribute Reference',
                                                      [from_attr, self.ref2_source['class'], to_attr,
                                                       self.ref2_target['class'], self.relationship.domain.name,
                                                       self.relationship.rnum, 'P', self.ref1['id']])