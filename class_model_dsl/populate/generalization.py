"""
generalization.py – Convert parsed relationship to a relation
"""

import logging
from PyRAL.relvar import Relvar
from typing import TYPE_CHECKING
from class_model_dsl.mp_exceptions import LessThanTwoSubclassesInGeneralization

from class_model_dsl.populate.pop_types import \
    Generalization_i, Facet_i, Superclass_i, Subclass_i, Minimal_Partition_i


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
    def populate(cls, mmdb: 'Tk', domain, rnum: str, record):
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
        Relvar.insert(db=mmdb, relvar='Generalization', tuples=[
            Generalization_i(Rnum=cls.rnum, Domain=domain['name'], Superclass=cls.superclass)
        ])
        # Superclass
        Relvar.insert(db=mmdb, relvar='Facet', tuples=[
            Facet_i(Rnum=cls.rnum, Domain=domain['name'], Class=cls.superclass)
        ])
        Relvar.insert(db=mmdb, relvar='Superclass', tuples=[
            Superclass_i(Rnum=cls.rnum, Domain=domain['name'], Class=cls.superclass)
        ])
        for subclass in cls.subclasses:
            Relvar.insert(db=mmdb, relvar='Facet', tuples=[
                Facet_i(Rnum=cls.rnum, Domain=domain['name'], Class=subclass)
            ])
            Relvar.insert(db=mmdb, relvar='Subclass', tuples=[
                Subclass_i(Rnum=cls.rnum, Domain=domain['name'], Class=subclass)
            ])
        Relvar.insert(db=mmdb, relvar='Minimal_Partition', tuples=[
            Minimal_Partition_i(Rnum=cls.rnum, Domain=domain['name'],
            A_subclass=cls.subclasses[0], B_subclass=cls.subclasses[1])
        ])

        # Attribute References
        # # If abbreviated, expand <subclass> abbreviation to one explicit reference per subclass
        # if len(self.genrefs) == 1 and self.genrefs[0]['source']['class'] == '<subclass>':
        #     self.genrefs = [{'source': {'class': s, 'attrs': self.genrefs[0]['source']['attrs']},
        #                      'target': self.genrefs[0]['target'], 'id': self.genrefs[0]['id']} for s in self.subclasses]
        #
        # for ref in self.genrefs:
        #     self.relationship.domain.model.Insert('Reference',
        #                                           ['G', ref['source']['class'], ref['target']['class'],
        #                                            self.relationship.rnum,
        #                                            self.relationship.domain.name])
        #     # To satisfy SQL standard, we need to add the Ref attribute so that the foreign key
        #     # references the identifier of the Reference table
        #     self.relationship.domain.model.Insert('Generalization Reference',
        #                                           ['G', ref['source']['class'], ref['target']['class'],
        #                                            self.relationship.rnum,
        #                                            self.relationship.domain.name])
        #     self.relationship.domain.model.Insert('Formalizing Class Role',
        #                                           [self.relationship.rnum, ref['source']['class'],
        #                                            self.relationship.domain.name])
        #     # Create attribute references for each subclass -> superclass reference
        #     for from_attr, to_attr in zip(ref['source']['attrs'], ref['target']['attrs']):
        #         self.relationship.domain.model.Insert('Attribute Reference',
        #                                               [from_attr, ref['source']['class'], to_attr,
        #                                                ref['target']['class'], self.relationship.domain.name,
        #                                                self.relationship.rnum, 'G', ref['id']])
