"""
lineage.py – Compute all lineage instances and populate them
"""

import logging
from class_model_dsl.database.sm_meta_db import SMmetaDB as smdb
from sqlalchemy import select, and_
from typing import List, Set, Optional



def findSubclasses(grel: str, domain: str) -> Set[str]:
    """
    Return the set of all subclasses in the specified generalization

    :param grel:
    :param domain:
    :return:
    """
    subclass_t = smdb.MetaData.tables['Subclass']
    p = subclass_t.c.Class  # Ideally we would project on zero attributes, but SQL requires at least one
    r = and_(
        (subclass_t.c.Rnum == grel),
        (subclass_t.c.Domain == domain),
    )
    q = select(p).where(r)
    rows = smdb.Connection.execute(q).fetchall()
    return {r['Class'] for r in rows}


def isSubclass(grel: str, cname: str, domain: str) -> bool:
    subclass_t = smdb.MetaData.tables['Subclass']
    p = subclass_t.c.Rnum  # Ideally we would project on zero attributes, but SQL requires at least one
    r = and_(
        (subclass_t.c.Class == cname),
        (subclass_t.c.Rnum == grel),
        (subclass_t.c.Domain == domain),
    )
    q = select(p).where(r)
    # One returned row means it is a subclass, otherwise it must be a superclass
    row = smdb.Connection.execute(q).fetchone()
    return True if row else False


def findSuperclass(grel: str, domain: str) -> str:
    """
    Traverse the specified relationship and return the name of the superclass

    :param grel:  A generalization relationship rnum
    :param domain:  A the name of the domain
    :return:
    """
    superclass_t = smdb.MetaData.tables['Superclass']
    p = superclass_t.c.Class  # We need the name of that superclass class
    r = and_(
        (superclass_t.c.Rnum == grel),
        (superclass_t.c.Domain == domain),
    )
    q = select(p).where(r)
    # One returned row means it is a subclass, otherwise it must be a superclass
    row = smdb.Connection.execute(q).fetchone()
    return row['Class']

class Lineage:
    """
    Create all lineages for a domain
    """

    def __init__(self, domain):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.domain = domain
        self.walks = []
        self.xrels = set()
        self.xclasses = set()

        # Get all classes with at least one subclass facet and no superclass facets as: leaves

        subclass_t = smdb.MetaData.tables['Subclass']
        superclass_t = smdb.MetaData.tables['Superclass']
        psuper = [superclass_t.c.Class, superclass_t.c.Domain]
        psub = [subclass_t.c.Class, subclass_t.c.Domain]
        q = select(psub).except_(select(psuper))
        rows = smdb.Connection.execute(q).fetchall()
        self.leaf_classes = [r['Class'] for r in rows]
        for leaf in self.leaf_classes:
            self.xrels = set()
            self.xclasses = set()
            leafwalk = self.step(walk=[], cvisit=leaf, rvisit=None)
            self.walks.append(leafwalk)
        print()

    def step(self, walk: List, cvisit: str, rvisit: Optional[str] = None) -> List:
        """
        Advance one step in the walk and return the result

        :param walk:  The walk prior to the step
        :param cvisit: The class currently being visited
        :param rvisit: The relationship currently being traversed
        :return: The updated walk
        """

        walk.append(cvisit)  # Advance the walk by adding the visited class
        # self.xclasses.add(cvisit)  # Class has been visited
        # Now we figure out where and if we can take another step

        # Get all adjacent relationships, if any, on the civisit class that have not already been traversed
        facet_t = smdb.MetaData.tables['Facet']  # Could be either super or subclasses, so we search Facets
        p = facet_t.c.Rnum # We project on the rnums
        r = and_(
            (facet_t.c.Class == cvisit),
            (facet_t.c.Domain == self.domain.name),
        )  # Restrict on the cvisit class
        q = select(p).where(r)  # Get all Facets that cvisit participates in
        rows = smdb.Connection.execute(q).fetchall()
        # Grab the result being careful to exclude prior traversals so we don't walk around in circles!
        adj_rels = [r['Rnum'] for r in rows if r['Rnum'] not in self.xrels and r['Rnum'] != rvisit]

        # We have nowhere else to walk if cvisit does not participate in any new rels
        if not adj_rels:
            return walk

        # Create a set of all hops going up to a superclass
        uphops = {h for h in adj_rels if isSubclass(grel=h, cname=cvisit, domain=self.domain.name) }

        # We can try to take a step
        for arel in adj_rels:
            # Is cvisit a superclass or subclass in this arel?
            # There are only two possibilities, so we arbitrarily check to see if it paticipates as a subclass
            if arel in uphops:  # Hopping up to a superclass
                superclass = findSuperclass(grel=arel, domain=self.domain.name)

                # Exclude all subclasses of unvisited uphop rels other than cvisit
                other_uphops = uphops - self.xrels - {arel}
                for o in other_uphops:
                    subclasses = findSubclasses(grel=o, domain=self.domain.name)
                    exclude_subclasses = {c for c in subclasses if c != cvisit}
                    self.xclasses = self.xclasses.union(exclude_subclasses)

                # Since we don't need to branch out, we can now mark this arel as excluded
                self.xrels.add(arel)
                walk = self.step(walk=walk, cvisit=superclass, rvisit=arel)
            else:  # hopping down to a subclass
                print()
                # We are going to branch out to one or more subclasses
                # (Any of our subclasses adjacent to some excluded relationship cannot be added)
                # Get all the subclass class names
                subclasses = findSubclasses(grel=arel, domain=self.domain.name)
                visit_subs = subclasses.difference(self.xclasses)
                for s in visit_subs:
                    print()
                    # Start a new branch if there is more than one subclass to visit
                    fork = True if len(visit_subs) > 1 else False
                    if fork:
                        self.xrels = set()  # New branch, no excluded rels
                        branch = self.step(walk=[], cvisit=s, rvisit=arel)
                        if branch:
                            walk.append(branch)
                        else:
                            self.xclasses.remove(s)
                            print()
                    else:
                        walk = self.step(walk=walk, cvisit=s, rvisit=arel)
                self.xrels.add(arel)
        print()
        return walk