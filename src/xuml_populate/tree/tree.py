"""
tree.py – Functions that process tree elements
"""

from typing import List

def extract(tree: List) -> (List[str], bool):
    """
    A tree is represented as a list of strings and sublists.
    A single invocation grabs all strings up to the first sublist, and then invokes itself on that sublist.
    Eventually, a sublist is encountered that is simply a list of strings terminating the recursion.
    As each invocation returns, any visited sublist is deleted.

    Recursive execution of this function effects a left handed search through the tree
    to extract a flat branch as a list of strings only and to prune that branch from the source tree.

    Therefore, this function has a side effect of pruning the provided tree

    :param tree: A list of strings and sublists. It may be modified by this function.
    :return: The pruned branch and whether or not this invocation of extract encountered a terminal (string only list).
    The result is useful internally to terminate recursion, but of no value to the outside caller
    """
    pop = []  # population
    # If there are no sublists in the node, it is a terminal node and we can just return its contents
    if not any(isinstance(n, list) for n in tree):
        # print("Terminal node")
        return tree, True
    # Step through each node
    for i, n in enumerate(tree):
        # If the node is a string, just append it to the population
        if type(n) is str:
            pop.append(n)
        else:  # Otherwise it is nested and we extract a branch from it
            branch = extract(n)
            pop = pop + branch[0]  # Add the extracted branch to the population
            if branch[1]:  # the extracted branch was a terminal node (no deeper nesting)
                del tree[i]  # We delete it from the tree so we don't process it again
                # If the remaining tree is a parent with only one child, we can transform it into
                # a flat branch. This means we have ['n0', ['n1']] and we can flatten that into
                # [ 'n0', 'n1' ]. This keeps us from ending up with a childless parent.
                if len(tree) == 2 and len(tree[1]) == 1:
                    tree[1] = tree[1][0]
                # print()
            break  # Once we process a nested node, we don't go any further
    # print()
    return pop, False  # This is not a terminal node


pattern = ['A', 'B', ['C', ['D', 'E'], ['F']], ['G', 'H']]

lineages = []
if not any(isinstance(n, list) for n in pattern):
    lineages = pattern
else:
    while len(pattern) > 0 and any(isinstance(n, list) for n in pattern):
        lineages.append(extract(pattern)[0])
# print()