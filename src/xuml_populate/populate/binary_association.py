"""
binary_association.py – Process a parsed binary association to populate the metamodel db
"""

# System
import logging

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.exceptions.class_exceptions import MixedTargetID, ReferenceToNonIdentifier
from xuml_populate.populate.mmclass_nt import (Association_i, Binary_Association_i, Association_Class_i,
                                               Perspective_i, Asymmetric_Perspective_i, T_Perspective_i,
                                               P_Perspective_i, Reference_i, Formalizing_Class_Role_i,
                                               Association_Reference_i, Simple_Association_Reference_i,
                                               Referring_Class_i, Attribute_Reference_i,
                                               Association_Class_Reference_i, T_Reference_i, P_Reference_i
                                               )

_logger = logging.getLogger(__name__)


class BinaryAssociation:
    """
    Populate a Binary Association
    """

    def __init__(self, tr: str, domain: str, rnum: str, record):
        """
        Populate a Binary Association

        :param tr: The name of the open transaction
        :param domain: The domain name
        :param rnum: The relationship name
        :param record: The relationship parse record
        """

        self.rnum = rnum
        self.domain = domain

        self.t_side = record.get('t_side')
        self.p_side = record.get('p_side')
        self.ref1 = record.get('ref1')
        self.ref1_source = None if not self.ref1 else self.ref1['source']
        self.ref1_target = None if not self.ref1 else self.ref1['target']
        self.ref2 = record.get('ref2')  # Supplied only for an associative binary
        self.ref2_source = None if not self.ref2 else self.ref2['source']
        self.ref2_target = None if not self.ref2 else self.ref2['target']
        self.assoc_cname = record.get('assoc_cname')
        self.assoc_mult = record.get('assoc_mult')
        self.ref1_target_id = self.targetid(self.ref1_target)
        self.ref2_target_id = None if not self.ref2_target else self.targetid(self.ref2_target)

        # Populate
        _logger.info(f"Populating Binary Association [{self.rnum}]")
        Relvar.insert(db=mmdb, tr=tr, relvar='Association', tuples=[
            Association_i(Rnum=self.rnum, Domain=domain)
        ])
        Relvar.insert(db=mmdb, tr=tr, relvar='Binary_Association', tuples=[
            Binary_Association_i(Rnum=self.rnum, Domain=domain)
        ])

        if self.assoc_cname:
            Relvar.insert(db=mmdb, tr=tr, relvar='Association_Class', tuples=[
                Association_Class_i(Rnum=self.rnum, Class=self.assoc_cname, Domain=domain, Multiplicity=self.assoc_mult)
            ])

        # Populate the T and P perspectives of an asymmetric binary association
        t_mult = self.t_side['mult'][0]
        Relvar.insert(db=mmdb, tr=tr, relvar='Perspective', tuples=[
            Perspective_i(Side='T', Rnum=self.rnum, Domain=domain,
                          Viewed_class=self.t_side['cname'], Phrase=self.t_side['phrase'],
                          Conditional=True if 'c' in self.t_side['mult'] else False,
                          Multiplicity=t_mult
                          )
        ])

        Relvar.insert(db=mmdb, tr=tr, relvar='Asymmetric_Perspective', tuples=[
            Asymmetric_Perspective_i(Side='T', Rnum=self.rnum, Domain=domain)
        ])
        Relvar.insert(db=mmdb, tr=tr, relvar='T_Perspective', tuples=[
            T_Perspective_i(Side='T', Rnum=self.rnum, Domain=domain)
        ])

        p_mult = self.p_side['mult'][0]
        Relvar.insert(db=mmdb, tr=tr, relvar='Perspective', tuples=[
            Perspective_i(Side='P', Rnum=self.rnum, Domain=domain,
                          Viewed_class=self.p_side['cname'], Phrase=self.p_side['phrase'],
                          Conditional=True if 'c' in self.p_side['mult'] else False,
                          Multiplicity=p_mult
                          )
        ])

        Relvar.insert(db=mmdb, tr=tr, relvar='Asymmetric_Perspective', tuples=[
            Asymmetric_Perspective_i(Side='P', Rnum=self.rnum, Domain=domain)
        ])
        Relvar.insert(db=mmdb, tr=tr, relvar='P_Perspective', tuples=[
            P_Perspective_i(Side='P', Rnum=self.rnum, Domain=domain)
        ])

        if not self.ref2:  # Simple binary association
            Relvar.insert(db=mmdb, tr=tr, relvar='Reference', tuples=[
                Reference_i(Ref='R',
                            From_class=self.ref1_source['class'], To_class=self.ref1_target['class'],
                            Rnum=self.rnum, Domain=domain)
            ])
            referenced_perspective = 'T' if self.ref1_target['class'] == self.t_side['cname'] else 'P'
            Relvar.insert(db=mmdb, tr=tr, relvar='Association_Reference', tuples=[
                Association_Reference_i(Ref_type='R',
                                        From_class=self.ref1_source['class'], To_class=self.ref1_target['class'],
                                        Rnum=self.rnum, Domain=domain,
                                        Perspective=referenced_perspective)
            ])
            Relvar.insert(db=mmdb, tr=tr, relvar='Simple_Association_Reference', tuples=[
                Simple_Association_Reference_i(Ref_type='R',
                                               From_class=self.ref1_source['class'], To_class=self.ref1_target['class'],
                                               Rnum=self.rnum, Domain=domain)
            ])
            Relvar.insert(db=mmdb, tr=tr, relvar='Referring_Class', tuples=[
                Referring_Class_i(Class=self.ref1_source['class'], Rnum=self.rnum, Domain=domain)
            ])
            Relvar.insert(db=mmdb, tr=tr, relvar='Formalizing_Class_Role', tuples=[
                Formalizing_Class_Role_i(Class=self.ref1_source['class'], Rnum=self.rnum, Domain=domain)
            ])

            # Simple Attribute Reference
            for from_attr, to_attr in zip(self.ref1_source['attrs'], self.ref1_target['attrs']):
                Relvar.insert(db=mmdb, tr=tr, relvar='Attribute_Reference', tuples=[
                    Attribute_Reference_i(From_attribute=from_attr, From_class=self.ref1_source['class'],
                                          To_attribute=to_attr, To_class=self.ref1_target['class'],
                                          Ref='R',
                                          Domain=domain, To_identifier=self.ref1_target_id, Rnum=self.rnum)
                ])
        else:  # Binary associative (with association class)
            # T Reference
            Relvar.insert(db=mmdb, tr=tr, relvar='Reference', tuples=[
                Reference_i(Ref='T',
                            From_class=self.ref1_source['class'], To_class=self.ref1_target['class'],
                            Rnum=self.rnum, Domain=domain)
            ])
            Relvar.insert(db=mmdb, tr=tr, relvar='Formalizing_Class_Role', tuples=[
                Formalizing_Class_Role_i(Class=self.ref1_source['class'], Rnum=self.rnum, Domain=domain)
            ])
            Relvar.insert(db=mmdb, tr=tr, relvar='Association_Reference', tuples=[
                Association_Reference_i(Ref_type='T',
                                        From_class=self.ref1_source['class'], To_class=self.ref1_target['class'],
                                        Rnum=self.rnum, Domain=domain,
                                        Perspective='T')
            ])
            Relvar.insert(db=mmdb, tr=tr, relvar='Association_Class_Reference', tuples=[
                Association_Class_Reference_i(Ref_type='T', Association_class=self.ref1_source['class'],
                                              Participating_class=self.ref1_target['class'],
                                              Rnum=self.rnum, Domain=domain)
            ])
            Relvar.insert(db=mmdb, tr=tr, relvar='T_Reference', tuples=[
                T_Reference_i(Ref_type='T', Association_class=self.ref1_source['class'],
                              Participating_class=self.ref1_target['class'],
                              Rnum=self.rnum, Domain=domain)
            ])

            # T Attribute References
            for from_attr, to_attr in zip(self.ref1_source['attrs'], self.ref1_target['attrs']):
                Relvar.insert(db=mmdb, tr=tr, relvar='Attribute_Reference', tuples=[
                    Attribute_Reference_i(From_attribute=from_attr, From_class=self.ref1_source['class'],
                                          To_attribute=to_attr, To_class=self.ref1_target['class'],
                                          Ref='T',
                                          Domain=domain, To_identifier=self.ref2_target_id, Rnum=self.rnum)
                ])

            # P Reference
            Relvar.insert(db=mmdb, tr=tr, relvar='Reference', tuples=[
                Reference_i(Ref='P',
                            From_class=self.ref2_source['class'], To_class=self.ref2_target['class'],
                            Rnum=self.rnum, Domain=domain)
            ])
            Relvar.insert(db=mmdb, tr=tr, relvar='Association_Reference', tuples=[
                Association_Reference_i(Ref_type='P',
                                        From_class=self.ref2_source['class'], To_class=self.ref2_target['class'],
                                        Rnum=self.rnum, Domain=domain,
                                        Perspective='P')
            ])
            Relvar.insert(db=mmdb, tr=tr, relvar='Association_Class_Reference', tuples=[
                Association_Class_Reference_i(Ref_type='P', Association_class=self.ref2_source['class'],
                                              Participating_class=self.ref2_target['class'],
                                              Rnum=self.rnum, Domain=domain)
            ])
            Relvar.insert(db=mmdb, tr=tr, relvar='P_Reference', tuples=[
                P_Reference_i(Ref_type='P', Association_class=self.ref2_source['class'],
                              Participating_class=self.ref2_target['class'],
                              Rnum=self.rnum, Domain=domain)
            ])

            # P Attribute References
            for from_attr, to_attr in zip(self.ref2_source['attrs'], self.ref2_target['attrs']):
                Relvar.insert(db=mmdb, tr=tr, relvar='Attribute_Reference', tuples=[
                    Attribute_Reference_i(From_attribute=from_attr, From_class=self.ref2_source['class'],
                                          To_attribute=to_attr, To_class=self.ref2_target['class'], Ref='P',
                                          Domain = domain, To_identifier = self.ref2_target_id, Rnum = self.rnum)
                ])

    def targetid(self, ref) -> int:
        # OR restriction criteria not yet supported in PyRAL, so we iterate on the attributes
        to_id = None
        for to_attr in ref['attrs']:
            R = f"Attribute:<{to_attr}>, Class:<{ref['class']}>, Domain:<{self.domain}>"
            result = Relation.restrict(db=mmdb, relation='Identifier_Attribute', restriction=R)
            if not result.body:
                _logger.exception(f"No identifier found in attribute reference on [{self.rnum}]")
                raise ReferenceToNonIdentifier
            attr_id = int(result.body[0]['Identifier'])
            if not to_id:
                to_id = attr_id
            elif to_id != attr_id:
                _logger.exception(f"Multiple identifiers referenced on [{self.rnum}]")
                raise MixedTargetID
        return to_id

