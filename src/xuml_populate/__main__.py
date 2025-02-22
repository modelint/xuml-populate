"""
Blueprint Model Repository Populator

"""
import logging
import logging.config
import sys
import argparse
from pathlib import Path
from xuml_populate.system import System
from xuml_populate import version

_logpath = Path("repo_pop.log")
_progname = 'Blueprint model repository populator'


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
    parser.add_argument('-A', '--actions', action='store_true',
                        help='Parse actions'),
    parser.add_argument('-V', '--version', action='store_true',
                        help='Print the current version of the repo populator')
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

    # System package specified
    if args.system:
        system_pkg_path = Path(args.system)
        s = System(system_path=system_pkg_path, parse_actions=args.actions)

    logger.info("No problemo")  # We didn't die on an exception, basically
    print("\nNo problemo")


if __name__ == "__main__":
    main()
