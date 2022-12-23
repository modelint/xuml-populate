"""
binary_association.py – Convert parsed relationship to a relation
"""

import logging
from PyRAL.relvar import Relvar
from typing import TYPE_CHECKING

from class_model_dsl.populate.pop_types import mult_tclral,\
    Association_i, Binary_Association_i, Association_Class_i, \
    Perspective_i, Asymmetric_Perspective_i, T_Perspective_i, P_Perspective_i

if TYPE_CHECKING:
    from tkinter import Tk

class BinaryAssociation:
    """
    Create a binary association relation
    """
    _logger = logging.getLogger(__name__)
    record = None
    rnum = None
    t_side, p_side = None, None
    ref1_source, ref2_source = None, None
    ref1_target, ref2_target = None, None
    ref1, ref2 = None, None
    assoc_cname = None
    assoc_mult = None

    @classmethod
    def populate(cls, mmdb: 'Tk', domain, rnum: str, record):
        """Constructor"""

        cls.rnum = rnum

        cls.t_side = record.get('t_side')
        cls.p_side = record.get('p_side')
        cls.ref1 = record.get('ref1')
        cls.ref1_source = None if not cls.ref1 else cls.ref1['source']
        cls.ref1_target = None if not cls.ref1 else cls.ref1['target']
        cls.ref2 = record.get('ref2')  # Supplied only for an associative binary
        cls.ref2_source = None if not cls.ref2 else cls.ref2['source']
        cls.ref2_target = None if not cls.ref2 else cls.ref2['target']
        cls.assoc_cname = record.get('assoc_cname')
        cls.assoc_mult = record.get('assoc_mult')

        # Populate
        cls._logger.info(f"Populating Binary Association [{cls.rnum}]")
        Relvar.insert(db=mmdb, relvar='Association', tuples=[
            Association_i(Rnum=cls.rnum, Domain=domain['name'])
        ])
        Relvar.insert(db=mmdb, relvar='Binary_Association', tuples=[
            Binary_Association_i(Rnum=cls.rnum, Domain=domain['name'])
        ])

        if cls.assoc_cname:
            Relvar.insert(db=mmdb, relvar='Association_Class', tuples=[
                Association_Class_i(Rnum=cls.rnum, Class=cls.assoc_cname, Domain=domain['name'])
            ])

        # Populate the T and P perspectives of an asymmetric binary association
        t_mult = cls.t_side['mult'][0]
        Relvar.insert(db=mmdb, relvar='Perspective', tuples=[
            Perspective_i(Side='T', Rnum=cls.rnum, Domain=domain['name'],
                          Viewed_class=cls.t_side['cname'], Phrase=cls.t_side['phrase'],
                          Conditional=True if 'c' in cls.t_side['mult'] else False,
                          Multiplicity= mult_tclral[t_mult]
                          )
        ])

        Relvar.insert(db=mmdb, relvar='Asymmetric Perspective', tuples=[
            Asymmetric_Perspective_i(Side='T', Rnum=cls.rnum, Domain=domain['name'])
        ])
        Relvar.insert(db=mmdb, relvar='T Perspective', tuples=[
            T_Perspective_i(Side='T', Rnum=cls.rnum, Domain=domain['name'])
        ])

        p_mult = cls.p_side['mult'][0]
        Relvar.insert(db=mmdb, relvar='Perspective', tuples=[
            Perspective_i(Side='P', Rnum=cls.rnum, Domain=domain['name'],
                          Viewed_class=cls.p_side['cname'], Phrase=cls.p_side['phrase'],
                          Conditional=True if 'c' in cls.p_side['mult'] else False,
                          Multiplicity= mult_tclral[p_mult]
                          )
        ])

        Relvar.insert(db=mmdb, relvar='Asymmetric Perspective', tuples=[
            Asymmetric_Perspective_i(Side='P', Rnum=cls.rnum, Domain=domain['name'])
        ])
        Relvar.insert(db=mmdb, relvar='P Perspective', tuples=[
            P_Perspective_i(Side='P', Rnum=cls.rnum, Domain=domain['name'])
        ])
        #
        #
        # # Create reference
        # if not self.ref2:  # Simple binary association
        #     self.relationship.domain.model.Insert('Reference',
        #                                           ['R', self.ref1_source['class'], self.ref1_target['class'],
        #                                            self.relationship.rnum,
        #                                            self.relationship.domain.name])
        #     referenced_perspective = 'T' if self.ref1_target['class'] == self.t_side['cname'] else 'P'
        #     self.relationship.domain.model.Insert('Association Reference',
        #                                           ['R', self.ref1_source['class'], self.ref1_target['class'],
        #                                            self.relationship.rnum,
        #                                            self.relationship.domain.name,
        #                                            referenced_perspective])
        #     # Add Ref type for SQL on R176
        #     self.relationship.domain.model.Insert('Simple Association Reference',
        #                                           ['R', self.ref1_source['class'], self.ref1_target['class'],
        #                                            self.relationship.rnum,
        #                                            self.relationship.domain.name])
        #     self.relationship.domain.model.Insert('Referring Class', [self.relationship.rnum, self.ref1_source['class'],
        #                                                               self.relationship.domain.name])
        #     self.relationship.domain.model.Insert('Formalizing Class Role',
        #                                           [self.relationship.rnum, self.ref1_source['class'],
        #                                            self.relationship.domain.name])
        #
        #     # Simple Attribute Reference
        #     for from_attr, to_attr in zip(self.ref1_source['attrs'], self.ref1_target['attrs']):
        #         self.relationship.domain.model.Insert('Attribute Reference',
        #                                               [from_attr, self.ref1_source['class'], to_attr,
        #                                                self.ref1_target['class'], self.relationship.domain.name,
        #                                                self.relationship.rnum, 'R', self.ref1['id']])
        # else:  # Binary associative (with association class)
        #     # T Reference
        #     self.relationship.domain.model.Insert('Reference',
        #                                           ['T', self.ref1_source['class'], self.ref1_target['class'],
        #                                            self.relationship.rnum,
        #                                            self.relationship.domain.name])
        #     self.relationship.domain.model.Insert('Formalizing Class Role', [self.relationship.rnum, self.assoc_cname,
        #                                                                      self.relationship.domain.name])
        #
        #     self.relationship.domain.model.Insert('Association Reference',
        #                                           ['T', self.ref1_source['class'], self.ref1_target['class'],
        #                                            self.relationship.rnum,
        #                                            self.relationship.domain.name,
        #                                            'T'])
        #     self.relationship.domain.model.Insert('Association Class Reference',
        #                                           ['T', self.ref1_source['class'], self.ref1_target['class'],
        #                                            self.relationship.rnum,
        #                                            self.relationship.domain.name])
        #     # Add Ref type for SQL on R153
        #     self.relationship.domain.model.Insert('T Reference',
        #                                           ['T', self.ref1_source['class'], self.ref1_target['class'],
        #                                            self.relationship.rnum,
        #                                            self.relationship.domain.name])
        #     # T Attribute References
        #     for from_attr, to_attr in zip(self.ref1_source['attrs'], self.ref1_target['attrs']):
        #         self.relationship.domain.model.Insert('Attribute Reference',
        #                                               [from_attr, self.ref1_source['class'], to_attr,
        #                                                self.ref1_target['class'], self.relationship.domain.name,
        #                                                self.relationship.rnum, 'T', self.ref1['id']])
        #
        #     # P Reference
        #     self.relationship.domain.model.Insert('Reference',
        #                                           ['P', self.ref2_source['class'], self.ref2_target['class'],
        #                                            self.relationship.rnum,
        #                                            self.relationship.domain.name])
        #     self.relationship.domain.model.Insert('Association Reference',
        #                                           ['P', self.ref2_source['class'], self.ref2_target['class'],
        #                                            self.relationship.rnum,
        #                                            self.relationship.domain.name,
        #                                            'P'])
        #     self.relationship.domain.model.Insert('Association Class Reference',
        #                                           ['P', self.ref2_source['class'], self.ref2_target['class'],
        #                                            self.relationship.rnum,
        #                                            self.relationship.domain.name])
        #     # Add Ref type for SQL on R153
        #     self.relationship.domain.model.Insert('P Reference',
        #                                           ['P', self.ref2_source['class'], self.ref2_target['class'],
        #                                            self.relationship.rnum,
        #                                            self.relationship.domain.name])
        #
        #     # P Attribute References
        #     for from_attr, to_attr in zip(self.ref2_source['attrs'], self.ref2_target['attrs']):
        #         self.relationship.domain.model.Insert('Attribute Reference',
        #                                               [from_attr, self.ref2_source['class'], to_attr,
        #                                                self.ref2_target['class'], self.relationship.domain.name,
        #                                                self.relationship.rnum, 'P', self.ref2['id']])