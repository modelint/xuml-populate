"""
generalization.py – Process parsed generalization to populate the metamodel db
"""

import logging
from pyral.relvar import Relvar
from xuml_populate.config import mmdb
from xuml_populate.mp_exceptions import LessThanTwoSubclassesInGeneralization

from xuml_populate.populate.mmclass_nt import \
    Generalization_i, Facet_i, Superclass_i, Subclass_i, Minimal_Partition_i, \
    Reference_i, Generalization_Reference_i, Formalizing_Class_Role_i, Attribute_Reference_i

_logger = logging.getLogger(__name__)


class Generalization:
    """
    Populate all relevant Generalization relvars
    """
    record = None
    rnum = None
    subclasses = None
    superclass = None
    genrefs = None

    @classmethod
    def populate(cls, tr: str, domain: str, rnum: str, record):
        """
        Populate a Generalization

        :param tr: The name of the open transaction
        :param domain: The domain name
        :param rnum: The relationship name
        :param record: The relationship parse record
        """
        cls.rnum = rnum

        cls.subclasses = record['subclasses']
        cls.superclass = record['superclass']
        cls.genrefs = record['genrefs']

        # First check for minimal partition
        # TODO We should be using the mmdb to check this constraint, here for now though
        if len(cls.subclasses) < 2:
            _logger.error(f"Less than two subclasses in [{cls.rnum}].")
            raise LessThanTwoSubclassesInGeneralization(rnum=cls.rnum)

        # Populate
        _logger.info(f"Populating Generalization [{cls.rnum}]")
        Relvar.insert(mmdb, tr=tr, relvar='Generalization', tuples=[
            Generalization_i(Rnum=cls.rnum, Domain=domain, Superclass=cls.superclass)
        ])
        # Superclass
        Relvar.insert(mmdb, tr=tr, relvar='Facet', tuples=[
            Facet_i(Rnum=cls.rnum, Domain=domain, Class=cls.superclass)
        ])
        Relvar.insert(mmdb, tr=tr, relvar='Superclass', tuples=[
            Superclass_i(Rnum=cls.rnum, Domain=domain, Class=cls.superclass)
        ])
        for subclass in cls.subclasses:
            Relvar.insert(mmdb, tr=tr, relvar='Facet', tuples=[
                Facet_i(Rnum=cls.rnum, Domain=domain, Class=subclass)
            ])
            Relvar.insert(mmdb, tr=tr, relvar='Subclass', tuples=[
                Subclass_i(Rnum=cls.rnum, Domain=domain, Class=subclass)
            ])
        Relvar.insert(mmdb, tr=tr, relvar='Minimal_Partition', tuples=[
            Minimal_Partition_i(Rnum=cls.rnum, Domain=domain,
                                A_subclass=cls.subclasses[0], B_subclass=cls.subclasses[1])
        ])

        # Attribute References
        # If abbreviated, expand <subclass> abbreviation to one explicit reference per subclass
        if len(cls.genrefs) == 1 and cls.genrefs[0]['source']['class'] == '<subclass>':
            cls.genrefs = [{'source': {'class': s, 'attrs': cls.genrefs[0]['source']['attrs']},
                            'target': cls.genrefs[0]['target'], 'id': cls.genrefs[0]['id']} for s in cls.subclasses]

        for ref in cls.genrefs:
            Relvar.insert(mmdb, tr=tr, relvar='Reference', tuples=[
                Reference_i(Ref='G',
                            From_class=ref['source']['class'], To_class=ref['target']['class'],
                            Rnum=cls.rnum, Domain=domain)
            ])
            Relvar.insert(mmdb, tr=tr, relvar='Generalization_Reference', tuples=[
                Generalization_Reference_i(Ref_type='G',
                                           Subclass=ref['source']['class'], Superclass=ref['target']['class'],
                                           Rnum=cls.rnum, Domain=domain)
            ])
            Relvar.insert(mmdb, tr=tr, relvar='Formalizing_Class_Role', tuples=[
                Formalizing_Class_Role_i(Class=ref['source']['class'], Rnum=cls.rnum, Domain=domain)
            ])
            # Create attribute references for each subclass -> superclass reference
            for from_attr, to_attr in zip(ref['source']['attrs'], ref['target']['attrs']):
                Relvar.insert(mmdb, tr=tr, relvar='Attribute_Reference', tuples=[
                    Attribute_Reference_i(From_attribute=from_attr, From_class=ref['source']['class'],
                                          To_attribute=to_attr, To_class=ref['target']['class'],
                                          Ref='G',
                                          Domain=domain, To_identifier=ref['id'], Rnum=cls.rnum)
                ])
