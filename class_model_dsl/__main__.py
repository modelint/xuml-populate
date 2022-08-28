"""
xUML class model parser

"""
import sys
import argparse
from pathlib import Path
from class_model_dsl.xuml.class_model import ClassModel
from class_model_dsl import version

# Configure the expected parameters and actions for the argparse module
def parse(cl_input):
    parser = argparse.ArgumentParser(description='xUML class model parser')
    parser.add_argument('-m', '--model', action='store',
                        help='class model file name')
    parser.add_argument('-V', '--version', action='store_true',
                        help='Print the current version of parser')
    return parser.parse_args(cl_input)


def main():
    # Parse the command line args
    args = parse(sys.argv[1:])

    if args.version:
        # Just print the version and quit
        print(f'xUML class model parser version: {version}')
        sys.exit(0)

    # Model specified?
    if args.model:
        model_path = Path(args.model)

        # Generate the xuml class diagram (we don't do anything with the returned variable yet)
        ClassModel(
            path=model_path
        )

if __name__ == "__main__":
    main()
