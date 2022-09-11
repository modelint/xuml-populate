"""
relationship.py – Convert parsed relationship to a relation
"""

import logging


class Relationship:
    """
    Create a relationship relation
    """

    def __init__(self, domain, parse_data):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.domain = domain
        self.parse_data = parse_data
        self.rnum = parse_data['rnum']
        self.subclasses = parse_data.get('subclasses')
        self.superclass = parse_data.get('superclass')
        self.grefs = parse_data.get('grefs')

        self.t_side = parse_data.get('t_side')
        self.p_side = parse_data.get('p_side')
        self.ref1 = parse_data.get('ref1')
        self.ref1_source = None if not self.ref1 else self.ref1['source']
        self.ref1_target = None if not self.ref1 else self.ref1['target']
        self.ref2 = parse_data.get('ref2')  # Supplied only for an associative binary
        self.ref2_source = None if not self.ref2 else self.ref2['source']
        self.ref2_target = None if not self.ref2 else self.ref2['target']
        self.assoc_cname = parse_data.get('assoc_cname')
        self.assoc_mult = parse_data.get('assoc_mult')

        # Populate relationship
        self.domain.model.Insert('Relationship', [self.rnum, self.domain.name])
        self.domain.model.Insert('Association', [self.rnum, self.domain.name])
        self.domain.model.Insert('Binary Association', [self.rnum, self.domain.name])
        if self.assoc_cname:
            self.domain.model.Insert('Association Class', [self.rnum, self.assoc_cname, self.domain.name])

        # Populate the T and P perspectives of an asymmetric binary association
        self.domain.model.Insert('Perspective',
                                 ['T', self.rnum, self.domain.name, self.t_side['cname'], self.t_side['phrase'],
                                  True if 'c' in self.t_side['mult'] else False, self.t_side['mult'][0]]
                                 )
        self.domain.model.Insert('Asymmetric Perspective', ['T', self.rnum, self.domain.name])
        self.domain.model.Insert('T Perspective', [self.rnum, self.domain.name])

        self.domain.model.Insert('Perspective',
                                 ['P', self.rnum, self.domain.name, self.p_side['cname'], self.p_side['phrase'],
                                  True if 'c' in self.p_side['mult'] else False, self.p_side['mult'][0]]
                                 )
        self.domain.model.Insert('Asymmetric Perspective', ['P', self.rnum, self.domain.name])
        self.domain.model.Insert('P Perspective', [self.rnum, self.domain.name])

        # Create reference
        if not self.ref2:  # Simple binary association
            self.domain.model.Insert('Reference', ['R', self.ref1_source['class'], self.ref1_source['class'], self.rnum,
                                                   self.domain.name])
            referenced_perspective = 'T' if self.ref1_target['class'] == self.t_side['cname'] else 'P'
            self.domain.model.Insert('Association Reference',
                                     ['R', self.ref1_source['class'], self.ref1_target['class'], self.rnum,
                                      self.domain.name,
                                      referenced_perspective])
            self.domain.model.Insert('Simple Association Reference',
                                     [self.ref1_source['class'], self.ref1_target['class'], self.rnum,
                                      self.domain.name])
            self.domain.model.Insert('Referring Class', [self.rnum, self.ref1_source['class'], self.domain.name])
            self.domain.model.Insert('Formalizing Class Role', [self.rnum, self.ref1_source['class'], self.domain.name])

            # Simple Attribute Reference
            for from_attr, to_attr in zip(self.ref1_source['attrs'], self.ref1_target['attrs']):
                self.domain.model.Insert('Attribute Reference', [from_attr, self.ref1_source['class'], to_attr,
                                                                 self.ref1_target['class'], self.domain.name,
                                                                 self.rnum, 'R', self.ref1['id']])
            print()
        else:  # Binary associative (with association class)
            # T Reference
            self.domain.model.Insert('Reference', ['T', self.ref1_source['class'], self.ref1_target['class'], self.rnum,
                                                   self.domain.name])
            self.domain.model.Insert('Formalizing Class Role', [self.rnum, self.assoc_cname, self.domain.name])

            self.domain.model.Insert('Association Reference',
                                     ['T', self.ref1_source['class'], self.ref1_target['class'], self.rnum,
                                      self.domain.name,
                                      'T'])
            self.domain.model.Insert('Association Class Reference',
                                     ['T', self.ref1_source['class'], self.ref1_target['class'], self.rnum,
                                      self.domain.name])
            self.domain.model.Insert('T Reference',
                                     [self.ref1_source['class'], self.ref1_target['class'], self.rnum,
                                      self.domain.name])
            # T Attribute References
            for from_attr, to_attr in zip(self.ref1_source['attrs'], self.ref1_target['attrs']):
                self.domain.model.Insert('Attribute Reference', [from_attr, self.ref1_source['class'], to_attr,
                                                                 self.ref1_target['class'], self.domain.name,
                                                                 self.rnum, 'T', self.ref1['id']])


            # P Reference
            self.domain.model.Insert('Reference', ['P', self.ref2_source['class'], self.ref2_target['class'], self.rnum,
                                                   self.domain.name])
            self.domain.model.Insert('Association Reference',
                                     ['P', self.ref2_source['class'], self.ref2_target['class'], self.rnum,
                                      self.domain.name,
                                      'P'])
            self.domain.model.Insert('Association Class Reference',
                                     ['P', self.ref2_source['class'], self.ref2_target['class'], self.rnum,
                                      self.domain.name])
            self.domain.model.Insert('P Reference',
                                     [self.ref2_source['class'], self.ref1_target['class'], self.rnum,
                                      self.domain.name])

            # P Attribute References
            for from_attr, to_attr in zip(self.ref2_source['attrs'], self.ref2_target['attrs']):
                self.domain.model.Insert('Attribute Reference', [from_attr, self.ref2_source['class'], to_attr,
                                                                 self.ref2_target['class'], self.domain.name,
                                                                 self.rnum, 'P', self.ref1['id']])
            print()