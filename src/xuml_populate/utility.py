""" utility.py - Debug utilities """
from contextlib import redirect_stdout
from pyral.relvar import Relvar
from xuml_populate.config import mmdb

def print_mmdb():
    mmdb_printout = f"mmdb_debug.txt"
    with open(mmdb_printout, 'w') as f:
        with redirect_stdout(f):
            Relvar.printall(db=mmdb)
