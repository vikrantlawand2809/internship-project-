"""Short entry point for running the perfkit report."""

import sys

from perfkit.cli import main as perfkit_main


if __name__ == "__main__":
    arguments = sys.argv[1:]
    if arguments and arguments[0] != "report":
        arguments.insert(0, "report")
    raise SystemExit(perfkit_main(arguments))
