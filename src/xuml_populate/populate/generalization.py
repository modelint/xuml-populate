"""
generalization.py – Convert parsed relationship to a relation
"""

import logging
from pyral.relvar import Relvar
from typing import TYPE_CHECKING
from class_model_dsl.mp_exceptions import LessThanTwoSubclassesInGeneralization

from class_model_dsl.populate.pop_types import \
    Generalization_i, Facet_i, Superclass_i, Subclass_i, Minimal_Partition_i,\
    Reference_i, Generalization_Reference_i, Formalizing_Class_Role_i, Attribute_Reference_i


if TYPE_CHECKING:
    from tkinter import Tk

class Generalization:
    """
    Create a generalization relationship relation
    """
    _logger = logging.getLogger(__name__)
    record = None
    rnum = None
    subclasses = None
    superclass = None
    genrefs = None

    @classmethod
    def populate(cls, mmdb: 'Tk', domain: str, rnum: str, record):
        """Constructor"""

        cls.rnum = rnum

        cls.subclasses = record['subclasses']
        cls.superclass = record['superclass']
        cls.genrefs = record['genrefs']

        # First check for minimal partition
        # TODO We should be using the mmdb to check this constraint, here for now though
        if len(cls.subclasses) < 2:
            cls._logger.error(f"Less than two subclasses in [{cls.rnum}].")
            raise LessThanTwoSubclassesInGeneralization(rnum=cls.rnum)

        # Populate
        cls._logger.info(f"Populating Generalization [{cls.rnum}]")
        Relvar.insert(relvar='Generalization', tuples=[
            Generalization_i(Rnum=cls.rnum, Domain=domain, Superclass=cls.superclass)
        ])
        # Superclass
        Relvar.insert(relvar='Facet', tuples=[
            Facet_i(Rnum=cls.rnum, Domain=domain, Class=cls.superclass)
        ])
        Relvar.insert(relvar='Superclass', tuples=[
            Superclass_i(Rnum=cls.rnum, Domain=domain, Class=cls.superclass)
        ])
        for subclass in cls.subclasses:
            Relvar.insert(relvar='Facet', tuples=[
                Facet_i(Rnum=cls.rnum, Domain=domain, Class=subclass)
            ])
            Relvar.insert(relvar='Subclass', tuples=[
                Subclass_i(Rnum=cls.rnum, Domain=domain, Class=subclass)
            ])
        Relvar.insert(relvar='Minimal_Partition', tuples=[
            Minimal_Partition_i(Rnum=cls.rnum, Domain=domain,
            A_subclass=cls.subclasses[0], B_subclass=cls.subclasses[1])
        ])

        # Attribute References
        # If abbreviated, expand <subclass> abbreviation to one explicit reference per subclass
        if len(cls.genrefs) == 1 and cls.genrefs[0]['source']['class'] == '<subclass>':
            cls.genrefs = [{'source': {'class': s, 'attrs': cls.genrefs[0]['source']['attrs']},
                             'target': cls.genrefs[0]['target'], 'id': cls.genrefs[0]['id']} for s in cls.subclasses]

        for ref in cls.genrefs:
            Relvar.insert(relvar='Reference', tuples=[
                Reference_i(Ref='G',
                            From_class=ref['source']['class'], To_class=ref['target']['class'],
                            Rnum=cls.rnum, Domain=domain)
            ])
            Relvar.insert(relvar='Generalization_Reference', tuples=[
                Generalization_Reference_i(Ref_type='G',
                            Subclass=ref['source']['class'], Superclass=ref['target']['class'],
                            Rnum=cls.rnum, Domain=domain)
            ])
            Relvar.insert(relvar='Formalizing_Class_Role', tuples=[
                Formalizing_Class_Role_i(Class=ref['source']['class'], Rnum=cls.rnum, Domain=domain)
            ])
            # Create attribute references for each subclass -> superclass reference
            for from_attr, to_attr in zip(ref['source']['attrs'], ref['target']['attrs']):
                Relvar.insert(relvar='Attribute_Reference', tuples=[
                    Attribute_Reference_i(From_attribute=from_attr, From_class=ref['source']['class'],
                                          To_attribute=to_attr, To_class=ref['target']['class'],
                                          Ref='G',
                                          Domain=domain, To_identifier=ref['id'], Rnum=cls.rnum)
                ])
