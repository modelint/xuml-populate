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
import yaml

print("Made it to here")

class Metamodel:

    _logger = logging.getLogger(__name__)
    metamodel_path = Path("class_model_dsl/metamodel/class-attribute.xcm")
    metamodel = None
    metamodel_subsystem = None
    types = None
    mult_tclral = {
        'M': '+',
        '1': '1',
        'Mc': '*',
        '1c': '?'
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
        # Skip imported classes
        if mm_class.get('import'):
            return

        cname = mm_class['name'].replace(' ', '_')
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
            cls.add_generalization(rel)
            return

        # Associative case if it refs 1 and 2 from an association class
        if rel.get('ref2'):
            cls.add_associative(rel)
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
        referring_class = source['class'].replace(' ', '_')
        referring_attrs = [a.replace(' ', '_') for a in source['attrs']]

        target = association['ref1']['target']
        referenced_class = target['class'].replace(' ', '_')
        referenced_attrs = [a.replace(' ', '_') for a in target['attrs']]

        # Find matching t or p side to obtain multiplicity
        if association['t_side']['cname'] == referring_class:
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
    def add_associative(cls, rel):
        """
        Add association constraint to metamodel db
        This will result in an association in TclRAL and possibly a correlation

        :param mm_class:
        :return:
        """
        pass
        #Database.create_correlation(name=rnum, )

    @classmethod
    def add_generalization(cls, rel):
        """
        Add association constraint to metamodel db
        This will result in an association in TclRAL and possibly a correlation

        :param mm_class:
        :return:
        """
        pass
        #Database.create_partition(name=rnum, )

    def Insert(self, table_name, instance):
        """Insert the instance in the named table dictionary"""
        pass
        # instance_dict = dict(
        #     zip(self.table_headers[table_name], instance)
        # )
        # self.population[table_name].append(instance_dict)

