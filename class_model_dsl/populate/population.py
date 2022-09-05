"""
population.py – All relations to be assigned to the db
"""

from class_model_dsl.database.sm_meta_db import SMmetaDB
import logging

class Population:
    """
    Build population to load into the db
    """

    def __init__(self):
        """Constructor"""
        self.logger = logging.getLogger(__name__)
        self.Relations = {k: [] for k in SMmetaDB.Relvars.keys()}