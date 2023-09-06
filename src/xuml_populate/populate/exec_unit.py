""" exec_unit.py - Process a Scrall Execution Unit"""

import logging
from scrall.parse.visitor import Execution_Unit_a
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tkinter import Tk

class ExecutionUnit:
    """
    Process an Execution Unit
    """
    _logger = logging.getLogger(__name__)

    @classmethod
    def process_method(cls, mmdb: 'Tk', cname: str, method: str, anum: str, xunit: Execution_Unit_a,
                       domain: str, scrall_text: str):
        pass
