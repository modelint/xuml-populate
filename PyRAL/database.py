"""
database.py -- TclRAL Database
"""
import logging
import tkinter

logger = logging.getLogger(__name__)
db = tkinter.Tcl()
db.eval("source tcl_scripts/init_TclRAL.tcl")
logger.info("Created a TclRAL db")
