"""
lineage.py – Compute all lineage instances and populate them
"""

import logging
from xuml_populate.config import mmdb
from typing import List, Set, Optional
from xuml_populate.tree.tree import extract
from xuml_populate.populate.mmclass_nt import Element_i, Spanning_Element_i, Lineage_i, Class_In_Lineage_i
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from pyral.relation import Relation

_logger = logging.getLogger(__name__)

tr_Lin = "Lineage"

class Lineage:
    """
    Create all lineages for a domain
    """

    domain = None

    lnums = 0
    walks = []
    xrels = set()
    xclasses = set()
    popclasses = set()
    lineages = None

    @classmethod
    def Derive(cls, domain: str):
        """

        :param domain:
        :return:
        """
        cls.domain = domain

        # Get all classes with at least one subclass facet and no superclass facets
        # These constitute 'leaves'. We use them as starting points as we step through a set of generalizations
        # to identify lineages.

        Relation.project(mmdb, attributes=('Class', 'Domain'), relation='Subclass', svar_name='subs')
        Relation.project(mmdb, attributes=('Class', 'Domain'), relation='Superclass', svar_name='supers')
        leaf_tuples = Relation.subtract(mmdb, rname1='subs', rname2='supers')
        leaf_classes = [t['Class'] for t in leaf_tuples.body]

        # Now we walk (step) through each generalization to build trees of one or more lineages
        for leaf in leaf_classes:
            cls.xrels = set()
            cls.xclasses = set()
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

        # Finally, we load each lineage into the tclral
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

        walk.append(cvisit)  # Advance the walk by adding the visited class
        cls.xclasses.add(cvisit)  # Class has been visited

        # Now we figure out where and if we can take another step

        # Get all adjacent relationships, if any, on the civisit class that have not already been traversed
        # Could be either superclass_name or subclasses, so we search Facets
        # Get all Facets that cvisit participates in
        R = f"Class:<{cvisit}>, Domain:<{cls.domain}>"
        Relation.restrict(mmdb, restriction=R, relation="Facet")
        s = Relation.project(mmdb, attributes=("Rnum", ))
        # Grab the result being careful to exclude prior traversals so we don't walk around in circles!
        adj_rels = [r['Rnum'] for r in s.body if r['Rnum'] not in cls.xrels and r['Rnum'] != rvisit]

        # We have nowhere else to walk if cvisit does not participate in any new rels
        if not adj_rels:
            return walk

        # Create a set of all hops going up to a superclass
        uphops = {h for h in adj_rels if cls.isSubclass(grel=h, cname=cvisit)}
        pass

        # We can try to take a step
        for arel in adj_rels:
            # Is cvisit a superclass or subclass in this arel?
            # There are only two possibilities, so we arbitrarily check to see if it paticipates as a subclass
            if arel in uphops:  # Hopping up to a superclass
                superclass = cls.findSuperclass(grel=arel)

                # Exclude all subclasses of unvisited uphop rels other than cvisit
                other_uphops = uphops - cls.xrels - {arel}
                for o in other_uphops:
                    subclasses = cls.findSubclasses(grel=o)
                    exclude_subclasses = {c for c in subclasses if c != cvisit}
                    cls.xclasses = cls.xclasses.union(exclude_subclasses)

                # Since we don't need to branch out, we can now mark this arel as excluded
                cls.xrels.add(arel)
                walk = cls.step(walk=walk, cvisit=superclass, rvisit=arel)
            else:  # hopping down to a subclass
                # We are going to branch out to one or more subclasses
                # (Any of our subclasses adjacent to some excluded relationship cannot be added)
                # Get all the subclass class names
                subclasses = cls.findSubclasses(grel=arel)
                visit_subs = subclasses.difference(cls.xclasses)
                for s in visit_subs:
                    # Start a new branch if there is more than one subclass to visit
                    fork = True if len(visit_subs) > 1 else False
                    if fork:
                        cls.xrels = set()  # New branch, no excluded rels
                        branch = cls.step(walk=[], cvisit=s, rvisit=arel)
                        if branch:
                            walk.append(branch)
                        else:
                            cls.xclasses.remove(s)
                    else:
                        walk = cls.step(walk=walk, cvisit=s, rvisit=arel)
                cls.xrels.add(arel)
        return walk

    @classmethod
    def findSubclasses(cls, grel: str) -> Set[str]:
        """
        Return the set of all subclasses in the specified generalization

        :param grel:
        :param domain:
        :return:
        """
        Relation.restrict(mmdb, relation='Subclass', restriction=f"Rnum:<{grel}>, Domain:<{cls.domain}>")
        s = Relation.project(mmdb, attributes=('Class', ))

        return {t['Class'] for t in s}

    @classmethod
    def isSubclass(cls, grel: str, cname: str) -> bool:
        Relation.restrict(mmdb,
                          relation='Subclass',
                          restriction=f"Class:<{cname}>, Rnum:<{grel}>, Domain:<{cls.domain}>")
        s = Relation.project(mmdb, attributes=())
        return bool(s.body)

    @classmethod
    def findSuperclass(cls, grel: str) -> str:
        """
        Traverse the specified relationship and return the name of the superclass

        :param grel:  A generalization relationship rnum
        :param domain:  A the name of the domain
        :return:
        """
        Relation.restrict(mmdb, relation='Superclass', restriction=f"Rnum:<{grel}>, Domain:<{cls.domain}>")
        s = Relation.project(mmdb, attributes=("Class", ))
        return s.body[0]['Class']

    @classmethod
    def populate(cls):
        """
        Trace through walks to populate all Lineages

        :return:
        """
        for lin in cls.lineages:
            cls.lnums += 1
            lnum = 'L' + (str(cls.lnums))
            _logger.info(f"Populating lineage [{lnum}]")
            Transaction.open(mmdb, tr_Lin)
            Relvar.insert(mmdb, tr=tr_Lin, relvar='Element', tuples=[
                Element_i(Label=lnum, Domain=cls.domain)
            ])
            Relvar.insert(mmdb, tr=tr_Lin, relvar='Spanning_Element', tuples=[
                Spanning_Element_i(Label=lnum, Domain=cls.domain)
            ])
            Relvar.insert(mmdb, tr=tr_Lin, relvar='Lineage', tuples=[
                Lineage_i(Lnum=lnum, Domain=cls.domain)
            ])
            for cname in lin.split(':'):
                Relvar.insert(mmdb, tr=tr_Lin, relvar='Class_In_Lineage', tuples=[
                    Class_In_Lineage_i(Class=cname,Lnum=lnum, Domain=cls.domain)
                ])
            Transaction.execute(mmdb, tr_Lin)
