"""
mm_class.py – Convert parsed class to a relation
"""

import logging
# from typing import TYPE_CHECKING
#
# if TYPE_CHECKING:
#     from class_model_dsl.xuml.class_model import ClassModel

class MMclass:
    """
    Create a class relation
    """

    def __init__(self, model, class_data):
        """Constructor"""
        self.logger = logging.getLogger(__name__)

        self.model = model
        self.class_data = class_data
        self.name = class_data['name']
        self.attributes = class_data['attributes']

        class_values = dict(zip(self.model.table_headers['Class'],
                                [self.class_data['name'], self.model.scope['domain']]))
        self.model.population['Class'].append(class_values)
