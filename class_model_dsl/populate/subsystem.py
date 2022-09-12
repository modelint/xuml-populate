"""
subsystem.py – Convert parsed subsystem to a relation
"""

import logging
from class_model_dsl.mp_exceptions import CnumsExceeded, LnumsExceeded

class Subsystem:
    """
    Create a subsystem relation
    """

    def __init__(self, domain, parse_data):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.domain = domain
        self.parse_data = parse_data
        self.name = parse_data['name']
        self.alias = parse_data['alias']
        self.range = parse_data['range']
        self.cnum = self.range[0]
        self.lnum = self.range[0]

        # Insert the subsystem relation
        self.domain.model.population['Subsystem'] = [
            {'Name': self.name}, {'First element number': self.range[0]},
            {'Domain': self.domain.name}, {'Alias': self.alias} ]
        self.domain.model.population['Domain Partition'] = [{'Number': self.range[0]}, {'Domain': self.domain.name}]

        # Note that we are creating a partition for the lowest boundary only
        # Even though the user has expressed both a low and high value. We ignore th high value (range[1])
        # So if you have two subsystems with ranges 1-99 and 100-199, this results in partions 1, 100
        # since the low number is inclusive and the upper bound is the next higher bound-1
        # This policy prevents any subsystem numbering overlap
        # See the relevant github wiki model descriptions on the SM Metamodel repository for more detail

    def next_cnum(self):
        if self.cnum <= self.range[1]:
            self.cnum += 1
            return "C"+str(self.cnum-1)
        else:
            self.logger.error(f"Max cnums {self.range[1]} exceeded in subsystem: {self.name}")
            raise CnumsExceeded(self.range[1])

    def next_lnum(self):
        if self.lnum <= self.range[1]:
            self.lnum += 1
            return "L"+str(self.lnum-1)
        else:
            self.logger.error(f"Max lnums {self.range[1]} exceeded in subsystem: {self.name}")
            raise LnumsExceeded(self.range[1])
