"""
traverse_action.py – Populate a traverse action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING, List, Set
from class_model_dsl.exceptions.action_exceptions import UndefinedRelationship, IncompletePath,\
    NoDestinationInPath, UndefinedClass, RelationshipUnreachableFromClass
from class_model_dsl.parse.scrall_visitor import PATH_a
from PyRAL.relation import Relation
from collections import namedtuple

Hop = namedtuple('Hop', 'cname rnum')

if TYPE_CHECKING:
    from tkinter import Tk

class TraverseAction:
    """
    Create all relations for a Traverse Action
    """
    _logger = logging.getLogger(__name__)

    source_flow = None
    dest_flow = None
    resolved_path = []
    id = None
    dest_class = None # End of path
    cursor_rel = None
    cursor_classes = None # Current set of from_classes
    source_class = None # Beginning of path
    hnum = 1 # Current hop number
    path_name = "" # Text representation of path as name
    from_class = None # Current hop
    mmdb = None
    domain = None

    @classmethod
    def validate_rel(cls, rnum: str):
        rel = f"Rnum:[{rnum}], Domain:[{cls.domain}]"
        if not Relation.restrict2(tclral=cls.mmdb, restriction=rel, relation="Relationship").body:
            cls._logger.error(f"Undefined Rnum {rnum} in Domain {cls.domain}")
            raise UndefinedRelationship(rnum, cls.domain)

    @classmethod
    def validate_rel_hop(cls, from_classes: Set[str], rnum: str) -> Set[str]:
        """
        Is the specified relationship associated/attached to the from_class?
        If so, return the set of classes that can be reached by that relationship.
        If the relationship is reflexive or ordinal, a from_class class may be included
        in the set of reachable classes.

        :param mmdb:
        :param rnum:
        :param from_classes: The set of classes that could be the start of this hop
        :param domain:
        :return: False if the relationship is not associated with the from_class
        """
        # Verify that the relationship is defined on the class model
        cls.validate_rel(rnum)

        # Verify that the relationship is attached to the from_class
        # Association or generalization? Check for a reference from or to the from_class
        rhop = f"(From_class:<{from_classes}> OR To_class:<{from_classes}>), Rnum:<{rnum}>, Domain:<{cls.domain}>"
        reachable_classes = set()
        if Relation.restrict3(tclral=cls.mmdb, restriction=rhop, relation="Reference").body:
            from_tos = Relation.project2(cls.mmdb, attributes=['From_class', 'To_class']).body
            # Reflexive association, from_class is both to and from, valid
            if len(from_tos) == 1 and set(from_tos[0].values() == {from_classes}):
                # the set of from_tos matches the fro
                return from_classes

            for t in from_tos:
                cnames = [n for n in t.values()]
                if from_class == cnames[0] == cnames[1]:
                    # Reflexive association, from_class is both to and from, valid
                    reachable_classes.add(from_class)
                    return reachable_classes
                if from_class == cnames[0]:
                    reachable_classes.add(cnames[1])
                else:
                    reachable_classes.add(cnames[0])
            return reachable_classes
        else:
            # Possibly an Ordinal which does not involve any Reference
            orhop = f"Ranked_class:[{from_class}], Rnum:[{rnum}, Domain:[{domain}]"
            if Relation.restrict2(tclral=mmdb, restriction=orhop, relation="Ordinal").body:
                reachable_classes.add(from_class)
                return reachable_classes

        # The relationship is not associated with the from_class
        raise RelationshipUnreachableFromClass(rnum, from_class, domain)

    @classmethod
    def rel_hop(cls, rnum:str):
        """
        Process an rnum found in a path
        :param rnum:
        :return:
        """
        # Ensure rel exists and is attached to one of the cursor classes
        reachable_classes = cls.validate_rel_hop(from_classes=cls.cursor_classes, rnum=rnum)
        # Move cursor to this validated rel
        cls.cursor_rel = rnum
        #
        if len(cls.cursor_classes) == 1:
            cls.resolved_path.append(Hop(cname=cls.cursor_classes.pop(), rnum=rnum))
        else:
            # for the current cursor rel, which of the cursor classes is reachable?
            c = reachable_classes.intersection(cls.cursor_classes)
            if c and c not in cls.cursor_classes:
                # If none, path is invalid
                raise
            # Otherwise, the one that is reachable becomes the new hop, append it
            cls.resolved_path.append(Hop(cname=c, rnum=rnum))
        cls.cursor_classes = reachable_classes

    @classmethod
    def build_path(cls, mmdb: 'Tk', source_class: str, domain: str, path: PATH_a):
        """
        Populate the entire Action

        :param mmdb:
        :param source_class:
        :param domain:
        :param path:
        :return:
        """
        cls.mmdb = mmdb
        cls.source_class = source_class # Source of first hop
        cls.cursor_classes = {source_class,} # Validation cursor is on this class now
        cls.domain = domain

        # Verify adequate path length
        if len(path.hops) < 2:
            raise IncompletePath(path)
        # Path has at least 2 hop elements

        # Validate destination class at the end of the path
        destination = path.hops[-1]
        if type(destination).__name__ != 'N_a':
            # Destination class must a name
            raise NoDestinationInPath(path)

        # Verify destination class is defined
        class_id = f'Name:[{destination.name}], Domain:[{domain}]'
        if not Relation.restrict2(mmdb, restriction=class_id, relation='Class').body:
            raise UndefinedClass(destination.name)

        # Destination class is valid
        cls.dest_class = destination.name

        # Valdiate path continuity
        # Step through the path validating each relationship, phrase, and class
        # Ensure that each step is reachable on the class model
        cursor = 0
        for hop in path.hops:
        # Instead, while cursor < len(path.hops):

            if type(hop).__name__ == 'N_a':
                # This is either a relationship phrase or a class name
                # First look for a class name
                class_id = {'Name': hop.name, 'Domain': domain}
                noclass = Relation.tuple_exists(mmdb, relation="Class", key=class_id)
                if noclass:
                    # Try a phrase name (and get Rnum, Viewed class
                    r = f"Phrase:{hop.name}, Domain: {domain}"
                    Relation.restrict(mmdb, relation='Perspective', restriction=r)
                    result = Relation.project(mmdb, attributes=['Rnum', 'Viewed_class'])
                    ptuples = Relation.make_pyrel(result).body
                    found = False
                    for t in ptuples:
                        pass



                # class_id = f"Name:{destination.name}, Domain:{domain_name}"
                # found_class = Relation.restrict(tclral=mmdb, restriction=class_id, relation="Class")
                # class_instance = Relation.make_pyrel(relation=found_class).body
                # But is this class reachable?
                # If rel is reflexive, this name must match the current hop source
                # Otherwise, determine type of relationship: gen, ordinal, association
                # If gen, destination must be a different class in the same generalization
                #   If same class, reject, if not rejected and in Facet, OK
                # If assoc and source-dest the same,


            if type(hop).__name__ == 'R_a':

                # Is it an association?
                # Get reference(s)
                # If one reference and Ref == R
                #   Create straight hop to other class (or same if reflexive)'
                #   break
                # Two refs T and P, associative hop
                #   Look ahead to next hop
                #   If Rnum or phrase:
                #      Get all reached classes of next hop and take intersection of
                #      reached classes to get destination
                #      break;
                #   Else name:
                #      If class name:
                #      That is the destination class, create the approriate
                #      hop subclass based on reference direction



                cls.rel_hop(rnum=hop.rnum)
                pass

                # Create Hop
                cls.path_name += f"/{hop.rnum}"




        pass
