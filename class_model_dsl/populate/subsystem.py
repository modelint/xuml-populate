"""
subsystem.py – Convert parsed subsystem to a relation
"""

import logging

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


        # Insert the subsystem relation
        self.domain.model.population['Subsystem'] = [
            {'Name': self.name}, {'First element number': self.range[0]},
            {'Domain': self.domain.name}, {'Alias': self.alias} ]
        self.domain.model.population['Domain Parition'] = [{'Number': self.range[0]}, {'Domain': self.domain.name}]

        # Note that we are creating a partition for the lowest boundary only
        # Even though the user has expressed both a low and high value. We ignore th high value (range[1])
        # So if you have two subsystems with ranges 1-99 and 100-199, this results in partions 1, 100
        # since the low number is inclusive and the upper bound is the next higher bound-1
        # This policy prevents any subsystem numbering overlap
        # See the relevant github wiki model descriptions on the SM Metamodel repository for more detail