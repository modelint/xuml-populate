"""
xUML class model parser

"""
import logging
import logging.config
import sys
import argparse
from pathlib import Path
from class_model_dsl.xuml.class_model import ClassModel
from class_model_dsl import version

_logpath = Path("mp.log")

def get_logger():
    """Initiate the logger"""
    log_conf_path = Path(__file__).parent / 'log.conf'  # Logging configuration is in this file
    logging.config.fileConfig(fname=log_conf_path, disable_existing_loggers=False)
    return logging.getLogger(__name__)  # Create a logger for this module


# Configure the expected parameters and actions for the argparse module
def parse(cl_input):
    parser = argparse.ArgumentParser(description='xUML class model parser')
    parser.add_argument('-m', '--model', action='store',
                        help='class model file name')
    parser.add_argument('-V', '--version', action='store_true',
                        help='Print the current version of parser')
    return parser.parse_args(cl_input)


def main():

    # Start logging
    logger = get_logger()
    logger.info(f'Model parser version: {version}')

    # Parse the command line args
    args = parse(sys.argv[1:])

    if args.version:
        # Just print the version and quit
        print(f'xUML class model parser version: {version}')
        sys.exit(0)

    # Model specified?
    if args.model:
        model_path = Path(args.model)

        # Parse the model
        ClassModel(
            path=model_path
        )

    logger.info("No problemo")  # We didn't die on an exception, basically


if __name__ == "__main__":
    main()
