"""
binary_association.py – Convert parsed relationship to a relation
"""

import logging
from PyRAL.relvar import Relvar
from typing import TYPE_CHECKING

from class_model_dsl.populate.pop_types import mult_tclral,\
    Association_i, Binary_Association_i, Association_Class_i, \
    Perspective_i, Asymmetric_Perspective_i, T_Perspective_i, P_Perspective_i,\
    Reference_i, Formalizing_Class_Role_i,\
    Association_Reference_i, Simple_Association_Reference_i, Referring_Class_i,\
    Attribute_Reference_i, Association_Class_Reference_i, T_Reference_i, P_Reference_i

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

        Relvar.insert(db=mmdb, relvar='Asymmetric_Perspective', tuples=[
            Asymmetric_Perspective_i(Side='T', Rnum=cls.rnum, Domain=domain['name'])
        ])
        Relvar.insert(db=mmdb, relvar='T_Perspective', tuples=[
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

        Relvar.insert(db=mmdb, relvar='Asymmetric_Perspective', tuples=[
            Asymmetric_Perspective_i(Side='P', Rnum=cls.rnum, Domain=domain['name'])
        ])
        Relvar.insert(db=mmdb, relvar='P_Perspective', tuples=[
            P_Perspective_i(Side='P', Rnum=cls.rnum, Domain=domain['name'])
        ])
        pass

        if not cls.ref2:  # Simple binary association
            Relvar.insert(db=mmdb, relvar='Reference', tuples=[
                Reference_i(Ref='R',
                            From_class=cls.ref1_source['class'], To_class=cls.ref1_target['class'],
                            Rnum=cls.rnum, Domain=domain['name'])
            ])
            referenced_perspective = 'T' if cls.ref1_target['class'] == cls.t_side['cname'] else 'P'
            Relvar.insert(db=mmdb, relvar='Association_Reference', tuples=[
                Association_Reference_i(Ref_type='R',
                                        From_class=cls.ref1_source['class'], To_class=cls.ref1_target['class'],
                                        Rnum=cls.rnum, Domain=domain['name'],
                                        Perspective=referenced_perspective)
            ])
            Relvar.insert(db=mmdb, relvar='Simple_Association_Reference', tuples=[
                Simple_Association_Reference_i(Ref_type='R',
                                               From_class=cls.ref1_source['class'], To_class=cls.ref1_target['class'],
                                               Rnum=cls.rnum, Domain=domain['name'])
            ])
            Relvar.insert(db=mmdb, relvar='Referring_Class', tuples=[
                Referring_Class_i(Class=cls.ref1_source['class'], Rnum=cls.rnum, Domain=domain['name'])
            ])
            Relvar.insert(db=mmdb, relvar='Formalizing_Class_Role', tuples=[
                Formalizing_Class_Role_i(Class=cls.ref1_source['class'], Rnum=cls.rnum, Domain=domain['name'])
            ])

            # Simple Attribute Reference
            for from_attr, to_attr in zip(cls.ref1_source['attrs'], cls.ref1_target['attrs']):
                Relvar.insert(db=mmdb, relvar='Attribute_Reference', tuples=[
                    Attribute_Reference_i(From_attribute=from_attr, From_class=cls.ref1_source['class'],
                                          To_attribute=to_attr, To_class=cls.ref1_target['class'],
                                          Ref='R',
                                          Domain=domain['name'], To_identifier=cls.ref1['id'], Rnum=cls.rnum)
                ])
        else:  # Binary associative (with association class)
            # T Reference
            Relvar.insert(db=mmdb, relvar='Reference', tuples=[
                Reference_i(Ref='T',
                            From_class=cls.ref1_source['class'], To_class=cls.ref1_target['class'],
                            Rnum=cls.rnum, Domain=domain['name'])
            ])
            Relvar.insert(db=mmdb, relvar='Formalizing_Class_Role', tuples=[
                Formalizing_Class_Role_i(Class=cls.ref1_source['class'], Rnum=cls.rnum, Domain=domain['name'])
            ])
            Relvar.insert(db=mmdb, relvar='Association_Reference', tuples=[
                Association_Reference_i(Ref_type='T',
                                    From_class=cls.ref1_source['class'], To_class=cls.ref1_target['class'],
                                    Rnum=cls.rnum, Domain=domain['name'],
                                    Perspective='T')
            ])
            Relvar.insert(db=mmdb, relvar='Association_Class_Reference', tuples=[
                Association_Class_Reference_i(Ref_type='T', Association_class=cls.ref1_source['class'],
                                              Participating_class=cls.ref1_target['class'],
                                              Rnum=cls.rnum, Domain=domain['name'])
            ])
            Relvar.insert(db=mmdb, relvar='T_Reference', tuples=[
                T_Reference_i(Ref_type='T', Association_class=cls.ref1_source['class'],
                                              Participating_class=cls.ref1_target['class'],
                                              Rnum=cls.rnum, Domain=domain['name'])
            ])

            # T Attribute References
            for from_attr, to_attr in zip(cls.ref1_source['attrs'], cls.ref1_target['attrs']):
                Relvar.insert(db=mmdb, relvar='Attribute_Reference', tuples=[
                    Attribute_Reference_i(From_attribute=from_attr, From_class=cls.ref1_source['class'],
                                          To_attribute=to_attr, To_class=cls.ref1_target['class'],
                                          Ref='T',
                                          Domain=domain['name'], To_identifier=cls.ref1['id'], Rnum=cls.rnum)
                ])

            # P Reference
            Relvar.insert(db=mmdb, relvar='Reference', tuples=[
                Reference_i(Ref='P',
                            From_class=cls.ref2_source['class'], To_class=cls.ref2_target['class'],
                            Rnum=cls.rnum, Domain=domain['name'])
            ])
            Relvar.insert(db=mmdb, relvar='Association_Reference', tuples=[
                Association_Reference_i(Ref_type='P',
                                        From_class=cls.ref2_source['class'], To_class=cls.ref2_target['class'],
                                        Rnum=cls.rnum, Domain=domain['name'],
                                        Perspective='P')
            ])
            Relvar.insert(db=mmdb, relvar='Association_Class_Reference', tuples=[
                Association_Class_Reference_i(Ref_type='P', Association_class=cls.ref2_source['class'],
                                              Participating_class=cls.ref2_target['class'],
                                              Rnum=cls.rnum, Domain=domain['name'])
            ])
            Relvar.insert(db=mmdb, relvar='P_Reference', tuples=[
                P_Reference_i(Ref_type='P', Association_class=cls.ref2_source['class'],
                              Participating_class=cls.ref2_target['class'],
                              Rnum=cls.rnum, Domain=domain['name'])
            ])

            # P Attribute References
            for from_attr, to_attr in zip(cls.ref2_source['attrs'], cls.ref2_target['attrs']):
                Relvar.insert(db=mmdb, relvar='Attribute_Reference', tuples=[
                    Attribute_Reference_i(From_attribute=from_attr, From_class=cls.ref2_source['class'],
                                          To_attribute=to_attr, To_class=cls.ref2_target['class'],
                                          Ref='P',
                                          Domain=domain['name'], To_identifier=cls.ref2['id'], Rnum=cls.rnum)
                ])