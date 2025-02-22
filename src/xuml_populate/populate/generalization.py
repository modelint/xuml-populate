"""
generalization.py – Process parsed generalization to populate the metamodel db
"""

# System
import logging

# Model Integration
from pyral.relvar import Relvar

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.reference import targetid
from xuml_populate.exceptions.mp_exceptions import LessThanTwoSubclassesInGeneralization
from xuml_populate.populate.mmclass_nt import (Generalization_i, Facet_i, Superclass_i, Subclass_i,
                                               Minimal_Partition_i, Reference_i, Generalization_Reference_i,
                                               Formalizing_Class_Role_i, Attribute_Reference_i)

_logger = logging.getLogger(__name__)


class Generalization:
    """
    Populate all relevant Generalization relvars
    """
    def __init__(self, tr: str, domain: str, rnum: str, record):
        """
        Populate a Generalization

        :param tr: The name of the open transaction
        :param domain: The domain name
        :param rnum: The relationship name
        :param record: The relationship parse record
        """
        self.rnum = rnum
        self.domain = domain

        self.subclasses = record['subclasses']
        self.superclass = record['superclass']
        self.genrefs = record['genrefs']
        self.targetid = targetid(ref=self.genrefs[0]['target'], rnum=self.rnum, domain=self.domain)

        # First check for minimal partition
        # TODO We should be using the mmdb to check this constraint, here for now though
        if len(self.subclasses) < 2:
            _logger.error(f"Less than two subclasses in [{self.rnum}].")
            raise LessThanTwoSubclassesInGeneralization(rnum=self.rnum)

        # Populate
        _logger.info(f"Populating Generalization [{self.rnum}]")
        Relvar.insert(db=mmdb, tr=tr, relvar='Generalization', tuples=[
            Generalization_i(Rnum=self.rnum, Domain=domain, Superclass=self.superclass)
        ])
        # Superclass
        Relvar.insert(db=mmdb, tr=tr, relvar='Facet', tuples=[
            Facet_i(Rnum=self.rnum, Domain=domain, Class=self.superclass)
        ])
        Relvar.insert(db=mmdb, tr=tr, relvar='Superclass', tuples=[
            Superclass_i(Rnum=self.rnum, Domain=domain, Class=self.superclass)
        ])
        for subclass in self.subclasses:
            Relvar.insert(db=mmdb, tr=tr, relvar='Facet', tuples=[
                Facet_i(Rnum=self.rnum, Domain=domain, Class=subclass)
            ])
            Relvar.insert(db=mmdb, tr=tr, relvar='Subclass', tuples=[
                Subclass_i(Rnum=self.rnum, Domain=domain, Class=subclass)
            ])
        Relvar.insert(db=mmdb, tr=tr, relvar='Minimal_Partition', tuples=[
            Minimal_Partition_i(Rnum=self.rnum, Domain=domain,
                                A_subclass=self.subclasses[0], B_subclass=self.subclasses[1])
        ])

        # Attribute References
        # If abbreviated, expand <subclass> abbreviation to one explicit reference per subclass
        if len(self.genrefs) == 1 and self.genrefs[0]['source']['class'] == '<subclass>':
            self.genrefs = [{'source': {'class': s, 'attrs': self.genrefs[0]['source']['attrs']},
                            'target': self.genrefs[0]['target'], 'id': self.targetid} for s in self.subclasses]

        for ref in self.genrefs:
            Relvar.insert(db=mmdb, tr=tr, relvar='Reference', tuples=[
                Reference_i(Ref='G',
                            From_class=ref['source']['class'], To_class=ref['target']['class'],
                            Rnum=self.rnum, Domain=domain)
            ])
            Relvar.insert(db=mmdb, tr=tr, relvar='Generalization_Reference', tuples=[
                Generalization_Reference_i(Ref_type='G',
                                           Subclass=ref['source']['class'], Superclass=ref['target']['class'],
                                           Rnum=self.rnum, Domain=domain)
            ])
            Relvar.insert(db=mmdb, tr=tr, relvar='Formalizing_Class_Role', tuples=[
                Formalizing_Class_Role_i(Class=ref['source']['class'], Rnum=self.rnum, Domain=domain)
            ])
            # Create attribute references for each subclass -> superclass reference
            for from_attr, to_attr in zip(ref['source']['attrs'], ref['target']['attrs']):
                Relvar.insert(db=mmdb, tr=tr, relvar='Attribute_Reference', tuples=[
                    Attribute_Reference_i(From_attribute=from_attr, From_class=ref['source']['class'],
                                          To_attribute=to_attr, To_class=ref['target']['class'],
                                          Ref='G',
                                          Domain=domain, To_identifier=self.targetid, Rnum=self.rnum)
                ])
