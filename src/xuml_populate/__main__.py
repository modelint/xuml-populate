"""
Blueprint Model Repository Populator

"""
# System
import logging
import logging.config
import sys
import argparse
from pathlib import Path
import atexit

# xUML Populate
from xuml_populate.system import System
from xuml_populate import version

_logpath = Path("modeldb.log")
_progname = 'Blueprint model repository populator'

def clean_up():
    """Normal and exception exit activities"""
    # Delete the log file
    _logpath.unlink(missing_ok=True)


def get_logger():
    """Initiate the logger"""
    log_conf_path = Path(__file__).parent / 'log.conf'  # Logging configuration is in this file
    logging.config.fileConfig(fname=log_conf_path, disable_existing_loggers=False)
    return logging.getLogger(__name__)  # Create a logger for this module


# Configure the expected parameters and actions for the argparse module
def parse(cl_input):
    parser = argparse.ArgumentParser(description=_progname)
    parser.add_argument('-s', '--system', action='store',
                        help='Name of the system package')
    parser.add_argument('-D', '--debug', action='store_true',
                        help='Debug mode'),
    parser.add_argument('-L', '--log', action='store_true',
                        help='Generate a diagnostic log file')
    parser.add_argument('-A', '--actions', action='store_true',
                        help='Suppress action language parsing'),
    parser.add_argument('-V', '--version', action='store_true',
                        help='Print the current version of the repo populator')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose messages')
    return parser.parse_args(cl_input)


def main():
    # Start logging
    logger = get_logger()
    logger.info(f'{_progname} version: {version}')

    # Parse the command line args
    args = parse(sys.argv[1:])

    if args.version:
        # Just print the version and quit
        print(f'{_progname} version: {version}')
        sys.exit(0)

    if not args.log:
        # If no log file is requested, remove the log file before termination
        atexit.register(clean_up)

    # A system package must be named and must exist
    if not args.system:
        print("No system specified. Use -s to name the system package to populate.", file=sys.stderr)
        sys.exit(1)

    system_pkg_path = Path(args.system).resolve()
    if not (system_pkg_path / 'system.yaml').is_file():
        print(f"No system package found at '{system_pkg_path}' (expected a directory containing system.yaml).",
              file=sys.stderr)
        sys.exit(1)

    # By default action language is parsed; -A suppresses it
    System(name=system_pkg_path.stem, system_path=system_pkg_path,
           parse_actions=not args.actions, verbose=args.verbose)

    logger.info("No problemo")  # We didn't die on an exception, basically
    if args.verbose:
        print("\nNo problemo")


if __name__ == "__main__":
    main()
