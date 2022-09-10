"""
relationship.py – Convert parsed relationship to a relation
"""

import logging


class Relationship:
    """
    Create a relationship relation
    """

    def __init__(self, domain, subsys, parse_data):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.domain = domain
        self.subsys = subsys
        self.parse_data = parse_data
        self.rnum = parse_data['rnum']
        self.t_side = parse_data['t_side']
        self.p_side = parse_data['p_side']

        # Populate relationship
        self.domain.model.Insert('Relationship', [self.rnum, self.domain.name])
        self.domain.model.Insert('Association', [self.rnum, self.domain.name])
        self.domain.model.Insert('Binary Association', [self.rnum, self.domain.name])

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
        print()
