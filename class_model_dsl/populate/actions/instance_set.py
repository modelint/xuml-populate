"""
instance_set.py – Break an instance set generator into one or more components
"""

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)

class InstanceSet:
    """
    Create all relations for a Traverse Action
    """

    @classmethod
    def process(cls, mmdb: 'Tk', instance_set_parse, only_one:bool=False, output_flow_name:Optional[str]=None,
                explicit_type:Optional[str]=None) -> str:
        """
        Given a parsed instance set expression, populate each component action
        and return the resultant Class Type name

        :param mmdb: The metamodel db
        :param instance_set_parse: A parsed instance set generator
        :param only_one: True means that at most one instance is generated, default assumes multiple are possible
        :param explicit_type: Optional declaration of the intended output type
        :param output_flow_name: Optional name of the output instance flow
        :return:  The name of the Class Type of the generated instance set
        """
        pass
