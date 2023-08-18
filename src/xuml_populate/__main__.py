"""
xUML domain parser

"""
import logging
import logging.config
import sys
import argparse
from pathlib import Path
from xuml_populate.user_model import UserModel
from xuml_populate import version

_logpath = Path("model_pop.log")
_progname = 'xUML repository populator'


def get_logger():
    """Initiate the logger"""
    log_conf_path = Path(__file__).parent / 'log.conf'  # Logging configuration is in this file
    logging.config.fileConfig(fname=log_conf_path, disable_existing_loggers=False)
    return logging.getLogger(__name__)  # Create a logger for this module


# Configure the expected parameters and actions for the argparse module
def parse(cl_input):
    parser = argparse.ArgumentParser(description=_progname)
    parser.add_argument('-d', '--domain', action='store',
                        help='Name of the domain package')
    parser.add_argument('-D', '--debug', action='store_true',
                        help='Debug mode'),
    parser.add_argument('-V', '--version', action='store_true',
                        help='Print the current version of parser')
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

    # User model domain package specified?
    if args.domain:
        domain_pkg_path = Path(args.domain)
        UserModel.load(domain_pkg_path)

    logger.info("No problemo")  # We didn't die on an exception, basically
    print("\nNo problemo")


if __name__ == "__main__":
    main()
