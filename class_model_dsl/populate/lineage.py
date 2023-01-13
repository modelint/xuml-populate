"""
lineage.py – Compute all lineage instances and populate them
"""

import logging
from typing import List, Set, Optional, TYPE_CHECKING
from class_model_dsl.tree.tree import extract
from collections import OrderedDict
from class_model_dsl.populate.pop_types import Element_i, Spanning_Element_i, Lineage_i, Class_in_Lineage_i
from PyRAL.transaction import Transaction
from PyRAL.relvar import Relvar
from PyRAL.relation import Relation

if TYPE_CHECKING:
    from tkinter import Tk

class Lineage:
    """
    Create all lineages for a domain
    """
    _logger = logging.getLogger(__name__)

    domain = None
    mmdb = None

    walks = []
    xrels = set()
    xclasses = set()
    popclasses = set()
    lineages = None

    @classmethod
    def Derive(cls, mmdb: 'Tk', domain: str):
        """

        :param mmdb:
        :param domain:
        :return:
        """
        cls.domain = domain
        cls.mmdb = mmdb

        # Get all classes with at least one subclass facet and no superclass facets
        # These constitute 'leaves'. We use them as starting points as we step through a set of generalizations
        # to identify lineages.

        Relation.project(db=mmdb, attributes=['Class', 'Domain'], relation='Subclass', svar_name='subs')
        Relation.project(db=mmdb, attributes=['Class', 'Domain'], relation='Superclass', svar_name='supers')
        r = Relation.subtract(db=mmdb, rname1='subs', rname2='supers')
        leaf_tuples = Relation.make_pyrel(relation=r, name='leaf tuples')
        leaf_classes = [t['Class'] for t in leaf_tuples.body]

        # Now we walk (step) through each generalization to build trees of one or more lineages
        for leaf in leaf_classes:
            xrels = set()
            xclasses = set()
            leafwalk = cls.step(walk=[], cvisit=leaf, rvisit=None)
            cls.walks.append(leafwalk)

        # We then prune these trees to extract unique branches, each of which constitutes a distinct lineage
        cls.lineages = set()
        for walk in cls.walks:
            pattern = walk.copy()
            if not any(isinstance(n, list) for n in pattern):
                pattern.sort()
                cls.lineages.add(':'.join(pattern))
            else:
                while len(pattern) > 0 and any(isinstance(n, list) for n in pattern):
                    extraction = extract(pattern)[0].copy()
                    extraction.sort()
                    cls.lineages.add(':'.join(extraction))

        # Finally, we load each lineage into the db
        cls.populate()


    @classmethod
    def step(cls, walk: List, cvisit: str, rvisit: Optional[str] = None) -> List:
        """
        Advance one step in the walk and return the result

        :param walk:  The walk prior to the step
        :param cvisit: The class currently being visited
        :param rvisit: The relationship currently being traversed
        :return: The updated walk
        """
        pass

        walk.append(cvisit)  # Advance the walk by adding the visited class
        cls.xclasses.add(cvisit)  # Class has been visited
        # Now we figure out where and if we can take another step

        # Get all adjacent relationships, if any, on the civisit class that have not already been traversed
        facet_t = smdb.MetaData.tables['Facet']  # Could be either superclass_name or subclasses, so we search Facets
        p = facet_t.c.Rnum  # We project on the rnums
        r = and_(
            (facet_t.c.Class == cvisit),
            (facet_t.c.Domain == self.domain.name),
        )  # Restrict on the cvisit class
        q = select(p).where(r)  # Get all Facets that cvisit participates in
        rows = smdb.Connection.execute(q).fetchall()
        # Grab the result being careful to exclude prior traversals so we don't walk around in circles!
        adj_rels = [r['Rnum'] for r in rows if r['Rnum'] not in self.xrels and r['Rnum'] != rvisit]

        # # We have nowhere else to walk if cvisit does not participate in any new rels
        # if not adj_rels:
        #     return walk
        #
        # # Create a set of all hops going up to a superclass
        # uphops = {h for h in adj_rels if isSubclass(grel=h, cname=cvisit, domain=self.domain.name)}
        #
        # # We can try to take a step
        # for arel in adj_rels:
        #     # Is cvisit a superclass or subclass in this arel?
        #     # There are only two possibilities, so we arbitrarily check to see if it paticipates as a subclass
        #     if arel in uphops:  # Hopping up to a superclass
        #         superclass = findSuperclass(grel=arel, domain=self.domain.name)
        #
        #         # Exclude all subclasses of unvisited uphop rels other than cvisit
        #         other_uphops = uphops - self.xrels - {arel}
        #         for o in other_uphops:
        #             subclasses = findSubclasses(grel=o, domain=self.domain.name)
        #             exclude_subclasses = {c for c in subclasses if c != cvisit}
        #             self.xclasses = self.xclasses.union(exclude_subclasses)
        #
        #         # Since we don't need to branch out, we can now mark this arel as excluded
        #         self.xrels.add(arel)
        #         walk = self.step(walk=walk, cvisit=superclass, rvisit=arel)
        #     else:  # hopping down to a subclass
        #         print()
        #         # We are going to branch out to one or more subclasses
        #         # (Any of our subclasses adjacent to some excluded relationship cannot be added)
        #         # Get all the subclass class names
        #         subclasses = findSubclasses(grel=arel, domain=self.domain.name)
        #         visit_subs = subclasses.difference(self.xclasses)
        #         for s in visit_subs:
        #             print()
        #             # Start a new branch if there is more than one subclass to visit
        #             fork = True if len(visit_subs) > 1 else False
        #             if fork:
        #                 self.xrels = set()  # New branch, no excluded rels
        #                 branch = self.step(walk=[], cvisit=s, rvisit=arel)
        #                 if branch:
        #                     walk.append(branch)
        #                 else:
        #                     self.xclasses.remove(s)
        #                     print()
        #             else:
        #                 walk = self.step(walk=walk, cvisit=s, rvisit=arel)
        #         self.xrels.add(arel)
        # print()
        return walk

    #     @classmethod
#     def findSubclasses(cls, grel: str, domain: str) -> Set[str]:
#         """
#         Return the set of all subclasses in the specified generalization
#
#         :param grel:
#         :param domain:
#         :return:
#         """
#         subclass_t = smdb.MetaData.tables['Subclass']
#         p = subclass_t.c.Class  # Ideally we would project on zero attributes, but SQL requires at least one
#         r = and_(
#             (subclass_t.c.Rnum == grel),
#             (subclass_t.c.Domain == domain),
#         )
#         q = select(p).where(r)
#         rows = smdb.Connection.execute(q).fetchall()
#         return {r['Class'] for r in rows}
#
#
# def isSubclass(grel: str, cname: str, domain: str) -> bool:
#     subclass_t = smdb.MetaData.tables['Subclass']
#     p = subclass_t.c.Rnum  # Ideally we would project on zero attributes, but SQL requires at least one
#     r = and_(
#         (subclass_t.c.Class == cname),
#         (subclass_t.c.Rnum == grel),
#         (subclass_t.c.Domain == domain),
#     )
#     q = select(p).where(r)
#     # One returned row means it is a subclass, otherwise it must be a superclass
#     row = smdb.Connection.execute(q).fetchone()
#     return True if row else False
#
#
# def findSuperclass(grel: str, domain: str) -> str:
#     """
#     Traverse the specified relationship and return the name of the superclass
#
#     :param grel:  A generalization relationship rnum
#     :param domain:  A the name of the domain
#     :return:
#     """
#     superclass_t = smdb.MetaData.tables['Superclass']
#     p = superclass_t.c.Class  # We need the name of that superclass class
#     r = and_(
#         (superclass_t.c.Rnum == grel),
#         (superclass_t.c.Domain == domain),
#     )
#     q = select(p).where(r)
#     # One returned row means it is a subclass, otherwise it must be a superclass
#     row = smdb.Connection.execute(q).fetchone()
#     return row['Class']
#
#
# class Lineage:
#     """
#     Create all lineages for a domain
#     """
#
#     @classmethod
#     def Derive(cls, mmdb: 'Tk', domain: str):
#         """Constructor"""
#         cls._logger = logging.getLogger(__name__)
#
#         self.domain = domain
#         self.walks = []
#         self.xrels = set()
#         self.xclasses = set()
#         self.popclasses = set()
#
#         # Get all classes with at least one subclass facet and no superclass facets
#         # These constitute 'leaves'. We use them as starting points as we step through a set of generalizations
#         # to identify lineages.
#         subclass_t = smdb.MetaData.tables['Subclass']
#         superclass_t = smdb.MetaData.tables['Superclass']
#         psuper = [superclass_t.c.Class, superclass_t.c.Domain]
#         psub = [subclass_t.c.Class, subclass_t.c.Domain]
#         q = select(psub).except_(select(psuper))
#         rows = smdb.Connection.execute(q).fetchall()
#         self.leaf_classes = [r['Class'] for r in rows]
#
#         # Now we walk (step) through each generalization to build trees of one or more lineages
#         for leaf in self.leaf_classes:
#             self.xrels = set()
#             self.xclasses = set()
#             leafwalk = self.step(walk=[], cvisit=leaf, rvisit=None)
#             self.walks.append(leafwalk)
#
#         # We then prune these trees to extract unique branches, each of which constitutes a distinct lineage
#         self.lineages = set()
#         for walk in self.walks:
#             pattern = walk.copy()
#             if not any(isinstance(n, list) for n in pattern):
#                 pattern.sort()
#                 self.lineages.add(':'.join(pattern))
#             else:
#                 while len(pattern) > 0 and any(isinstance(n, list) for n in pattern):
#                     extraction = extract(pattern)[0].copy()
#                     extraction.sort()
#                     self.lineages.add(':'.join(extraction))
#
#         # Finally, we load each lineage into the db
#         self.populate()
#
    @classmethod
    def populate(cls):
        """
        Trace through walks to populate all Lineages

        :return:
        """
        pass
#         population = OrderedDict({'Element': [], 'Spanning Element': [], 'Lineage': [], 'Class in Lineage': []})
#         for lin in self.lineages:
#             self.domain.lnums += 1
#             lnum = 'L' + (str(self.domain.lnums))
#             idvals = {'Number': lnum, 'Domain': self.domain.name}
#             population['Element'].append(idvals)
#             population['Spanning Element'].append(idvals)  # Element and Spanning Element have the same header
#             population['Lineage'].append({'Lnum': lnum, 'Domain': self.domain.name})
#             for cname in lin.split(':'):
#                 population['Class in Lineage'].append({'Class': cname, 'Lnum': lnum, 'Domain': self.domain.name})
#         pass
#         for relvar_name, relation in population.items():
#             t = smdb.Relvars[relvar_name]
#             smdb.Connection.execute(t.insert(), relation)
#
        # @classmethod
        # def step(cls, walk: List, cvisit: str, rvisit: Optional[str] = None) -> List:
#         """
#         Advance one step in the walk and return the result
#
#         :param walk:  The walk prior to the step
#         :param cvisit: The class currently being visited
#         :param rvisit: The relationship currently being traversed
#         :return: The updated walk
#         """
#
#         walk.append(cvisit)  # Advance the walk by adding the visited class
#         # self.xclasses.add(cvisit)  # Class has been visited
#         # Now we figure out where and if we can take another step
#
#         # Get all adjacent relationships, if any, on the civisit class that have not already been traversed
#         facet_t = smdb.MetaData.tables['Facet']  # Could be either superclass_name or subclasses, so we search Facets
#         p = facet_t.c.Rnum  # We project on the rnums
#         r = and_(
#             (facet_t.c.Class == cvisit),
#             (facet_t.c.Domain == self.domain.name),
#         )  # Restrict on the cvisit class
#         q = select(p).where(r)  # Get all Facets that cvisit participates in
#         rows = smdb.Connection.execute(q).fetchall()
#         # Grab the result being careful to exclude prior traversals so we don't walk around in circles!
#         adj_rels = [r['Rnum'] for r in rows if r['Rnum'] not in self.xrels and r['Rnum'] != rvisit]
#
#         # We have nowhere else to walk if cvisit does not participate in any new rels
#         if not adj_rels:
#             return walk
#
#         # Create a set of all hops going up to a superclass
#         uphops = {h for h in adj_rels if isSubclass(grel=h, cname=cvisit, domain=self.domain.name)}
#
#         # We can try to take a step
#         for arel in adj_rels:
#             # Is cvisit a superclass or subclass in this arel?
#             # There are only two possibilities, so we arbitrarily check to see if it paticipates as a subclass
#             if arel in uphops:  # Hopping up to a superclass
#                 superclass = findSuperclass(grel=arel, domain=self.domain.name)
#
#                 # Exclude all subclasses of unvisited uphop rels other than cvisit
#                 other_uphops = uphops - self.xrels - {arel}
#                 for o in other_uphops:
#                     subclasses = findSubclasses(grel=o, domain=self.domain.name)
#                     exclude_subclasses = {c for c in subclasses if c != cvisit}
#                     self.xclasses = self.xclasses.union(exclude_subclasses)
#
#                 # Since we don't need to branch out, we can now mark this arel as excluded
#                 self.xrels.add(arel)
#                 walk = self.step(walk=walk, cvisit=superclass, rvisit=arel)
#             else:  # hopping down to a subclass
#                 print()
#                 # We are going to branch out to one or more subclasses
#                 # (Any of our subclasses adjacent to some excluded relationship cannot be added)
#                 # Get all the subclass class names
#                 subclasses = findSubclasses(grel=arel, domain=self.domain.name)
#                 visit_subs = subclasses.difference(self.xclasses)
#                 for s in visit_subs:
#                     print()
#                     # Start a new branch if there is more than one subclass to visit
#                     fork = True if len(visit_subs) > 1 else False
#                     if fork:
#                         self.xrels = set()  # New branch, no excluded rels
#                         branch = self.step(walk=[], cvisit=s, rvisit=arel)
#                         if branch:
#                             walk.append(branch)
#                         else:
#                             self.xclasses.remove(s)
#                             print()
#                     else:
#                         walk = self.step(walk=walk, cvisit=s, rvisit=arel)
#                 self.xrels.add(arel)
#         print()
#         return walk
