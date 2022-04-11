"""
Package interface.

This is the main package interface.
"""
from signposting import cli
import sys

if __name__ == '__main__':
    exit = cli.main(*sys.argv[1:])
    sys.exit(exit)
