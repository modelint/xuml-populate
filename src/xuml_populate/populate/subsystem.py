"""
subsystem.py – Manage assignment of subsystem class and relationship numbers
"""

import logging
from xuml_populate.exceptions.mp_exceptions import CnumsExceeded


class Subsystem:
    """
    Manages the automatic assignment of unique numbers to the Subsystem's classes. In traditional Shlaer-Mellor,
    Cnums were assigned by the modeler for naming purposes just like Rnums. Here we assign and use the numbers
    internally only as a means of unique identification among all Subsystem Elements. This means that the number
    assigned to any given class may vary each time the model is populated.
    """

    def __init__(self, subsys_parse):
        """Constructor to initialize the cnum counter"""

        self._logger = logging.getLogger(__name__)

        self.name = subsys_parse['name']  # Name of the subsystem
        self.range = subsys_parse['range']  # Numbering range as a two element tuple
        self.cnum = self.range[0]  # Lowest assignable value in the range, we start counting here

    def next_cnum(self):
        """
        Assign the next available class number and throw an unrecoverable error if the numbering range is exceeded.
        """
        if self.cnum <= self.range[1]:
            self.cnum += 1
            return "C" + str(self.cnum - 1)
        else:
            self._logger.error(f"Max cnums {self.range[1]} exceeded in subsystem: {self.name}")
            raise CnumsExceeded(self.range[1])

