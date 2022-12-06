"""
metamodel.py – Parses the SM Metamodel and uses it to create a corresponding database schema

For now, we focus only on the Class and Attribute Subsystem
"""
import sys
import logging
from pathlib import Path
from class_model_dsl.parse.model_parser import ModelParser
from class_model_dsl.mp_exceptions import ModelParseError, MPIOException
from PyRAL.database import Database
from PyRAL.rtypes import Attribute
from PyRAL.database import Mult as DBMult
import yaml

print("Made it to here")


def unspace(sdelim: str) -> str:
    """
    :param sdelim: space delimited string
    :return: underscore delimited string
    """
    return sdelim.replace(' ', '_')


class Metamodel:
    _logger = logging.getLogger(__name__)
    metamodel_path = Path("class_model_dsl/metamodel/class-attribute.xcm")
    metamodel = None
    metamodel_subsystem = None
    types = None
    imported = set()
    mult_tclral = {
        'M': DBMult.AT_LEAST_ONE,
        '1': DBMult.EXACTLY_ONE,
        'Mc': DBMult.ZERO_ONE_OR_MANY,
        '1c': DBMult.ZERO_OR_ONE
    }

    @classmethod
    def create_db(cls):
        """
        Create a metamodel database in PyRAL complete with relvars and constraints
        from a parse of the metamodel xcm file
        :return:
        """
        # Create a TclRAL session
        Database.init()

        # Parse the metamodel
        cls.parse()

        # Create schema element in db for each class and relationship
        for c in cls.metamodel_subsystem.classes:
            cls.add_class(c)

        for r in cls.metamodel_subsystem.rels:
            cls.add_rel(r)
        pass

    @classmethod
    def parse(cls):
        """
        Parse the metamodel

        :return:
        """
        try:
            cls.metamodel = ModelParser(model_file_path=cls.metamodel_path, debug=False)
        except MPIOException as e:
            sys.exit(e)
        try:
            cls.metamodel_subsystem = cls.metamodel.parse()
        except ModelParseError as e:
            sys.exit(e)

        # Get the datatypes
        with open("class_model_dsl/metamodel/mm_types.yaml", 'r') as file:
            cls.types = yaml.safe_load(file)

    @classmethod
    def add_class(cls, mm_class):
        """
        Add class to database as a relvar definition

        :param mm_class:
        :return:
        """
        # Skip imported classes (we'll add them when their home subsystem is processed)
        if mm_class.get('import'):
            # Add name to the set of imported classes so that we can resolve them later
            cls.imported.add(mm_class['name'])
            return

        cname = unspace(mm_class['name'])
        attrs = [Attribute(name=a['name'], type=cls.types[a['type']]) for a in mm_class['attributes']]
        ids = {}
        for a in mm_class['attributes']:
            identifiers = a.get('I', [])  # This attr might not participate in any identifier
            for i in identifiers:
                if i[0] not in ids:
                    ids[i[0]] = [a['name']]
                else:
                    ids[i[0]].append(a['name'])
        Database.create_relvar(name=cname, attrs=attrs, ids=ids)

    @classmethod
    def add_rel(cls, rel):
        """
        Based on the rel type, call the appropriate method

        :param mm_class:
        :return:
        """
        # The following cases are mutually exclusive since an SM relationship
        # is either a generalization, associative (has association class),
        # or association relationship (no association class)

        # Generalization case if it has a superclass defined
        if rel.get('superclass'):
            cls.add_generalization(generalization=rel)
            return

        # Associative case if it refs 1 and 2 from an association class
        if rel.get('ref2'):
            cls.add_associative(associative_rel=rel)
            return

        # Association case not the other two cases (only one ref)
        cls.add_association(association=rel)

    @classmethod
    def add_association(cls, association):
        """
        Add association constraint to metamodel db
        This will result in an association in TclRAL and possibly a correlation

        From TclRAL man page
        relvar association name
            refrngRelvar refrngAttrList refToSpec
            refToRelvar refToAttrList refrngSpec

        Metamodel terminology
        relvar association <rnum> <referring_class> <ref> <mult> <referenced_class> <mult>

        example:
        relvar association R3 Domain_Partition Domain + Modeled_Domain Name 1

        :param rel:  The association
        """
        rnum = association['rnum']

        source = association['ref1']['source']
        if source['class'] in cls.imported:
            cls._logger.warning(f"Rel {rnum} to imported class skipped")
            return  # We'll add the association after all imported classes are resolved
        referring_class = unspace(source['class'])
        referring_attrs = [unspace(a) for a in source['attrs']]

        target = association['ref1']['target']
        if target['class'] in cls.imported:
            cls._logger.warning(f"Rel {rnum} to imported class skipped")
            return  # We'll add the association after all imported classes are resolved
        referenced_class = unspace(target['class'])
        referenced_attrs = [unspace(a) for a in target['attrs']]

        # Find matching t or p side to obtain multiplicity
        if association['t_side']['cname'] == source['class']:
            referring_mult = cls.mult_tclral[association['t_side']['mult']]
            referenced_mult = cls.mult_tclral[association['p_side']['mult']]
        else:
            referring_mult = cls.mult_tclral[association['p_side']['mult']]
            referenced_mult = cls.mult_tclral[association['t_side']['mult']]

        Database.create_association(name=rnum,
                                    from_relvar=referring_class, from_attrs=referring_attrs, from_mult=referring_mult,
                                    to_relvar=referenced_class, to_attrs=referenced_attrs, to_mult=referenced_mult,
                                    )

    @classmethod
    def add_associative(cls, associative_rel):
        """
        Add association constraint to metamodel db
        This will result in an association in TclRAL and possibly a correlation

        Example:
        relvar correlation C1 OWNERSHIP OwnerName + OWNER OwnerName DogName * DOG DogName

        :param associative_rel:
        """
        rnum = associative_rel['rnum']
        if associative_rel['assoc_cname'] in cls.imported:
            cls._logger.warning(f"Rel {rnum} to imported class skipped")
            return  # We'll add the association after all imported classes are resolved
        assoc_class = unspace(associative_rel['assoc_cname'])

        ref1_source = associative_rel['ref1']['source']
        ref1_from_attrs = [unspace(a) for a in ref1_source['attrs']]

        target1 = associative_rel['ref1']['target']
        if target1['class'] in cls.imported:
            cls._logger.warning(f"Rel {rnum} to imported class skipped")
            return  # We'll add the association after all imported classes are resolved
        ref1_class = unspace(target1['class'])
        ref1_to_attrs = [unspace(a) for a in target1['attrs']]

        ref2_source = associative_rel['ref2']['source']
        ref2_from_attrs = [unspace(a) for a in ref2_source['attrs']]

        target2 = associative_rel['ref2']['target']
        if target2['class'] in cls.imported:
            cls._logger.warning(f"Rel {rnum} to imported class skipped")
            return  # We'll add the association after all imported classes are resolved
        ref2_class = unspace(target2['class'])
        ref2_to_attrs = [unspace(a) for a in target2['attrs']]

        if associative_rel['t_side']['cname'] == associative_rel['ref1']['target']['class']:
            ref1_mult = cls.mult_tclral[associative_rel['t_side']['mult']]
            ref2_mult = cls.mult_tclral[associative_rel['p_side']['mult']]
        else:
            ref1_mult = cls.mult_tclral[associative_rel['p_side']['mult']]
            ref2_mult = cls.mult_tclral[associative_rel['t_side']['mult']]

        # Find matching t or p side to obtain multiplicity

        Database.create_correlation(name=rnum, correlation_relvar=assoc_class,
                                    correl_a_attrs=ref1_from_attrs, a_mult=ref1_mult, a_relvar=ref1_class,
                                    a_ref_attrs=ref1_to_attrs,
                                    correl_b_attrs=ref2_from_attrs, b_mult=ref2_mult, b_relvar=ref2_class,
                                    b_ref_attrs=ref2_to_attrs,
                                    )

    @classmethod
    def add_generalization(cls, generalization):
        """
        Add partition constraint to metamodel db

        :param mm_class:
        """
        rnum = generalization['rnum']
        if generalization['superclass'] in cls.imported:
            cls._logger.warning(f"Rel {rnum} to imported class skipped")
            return  # We'll add the association after all imported classes are resolved
        superclass_name = generalization['superclass']
        for n in generalization['subclasses']:
            if n in cls.imported:
                cls._logger.warning(f"Rel {rnum} to imported class skipped")
                return  # We'll add the association after all imported classes are resolved
        subclass_names = generalization['subclasses']
        if len(generalization['genrefs']) == 1:  # All superclass refs identical
            genref = generalization['genrefs'][0]
            superclass_attrs = [unspace(a) for a in genref['target']['attrs']]
            subclass_attrs = [unspace(a) for a in genref['source']['attrs']]
            subclasses = {unspace(s): subclass_attrs for s in subclass_names}
            pass
        else:
            # TODO: Put in logic for Non uniform superclass refs (no examples available in class-attr subsys)
            pass

        Database.create_partition(name=rnum, super=unspace(superclass_name),
                                  super_attrs=superclass_attrs, subs=subclasses)

    def Insert(self, table_name, instance):
        """Insert the instance in the named table dictionary"""
        pass
        # instance_dict = dict(
        #     zip(self.table_headers[table_name], instance)
        # )
        # self.population[table_name].append(instance_dict)
