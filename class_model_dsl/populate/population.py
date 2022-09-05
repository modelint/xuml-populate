"""
population.py – All relations to be assigned to the db
"""

from class_model_dsl.database.relvars import

class Population:
    """
    Build an identifier for a class
    """

    def __init__(self):
        """Constructor"""
        self.logger = logging.getLogger(__name__)
