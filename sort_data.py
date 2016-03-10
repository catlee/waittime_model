#!/usr/bin/env python
import json
import sys

from utils import output_event


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('filename', help='input filename (default stdin)', nargs='?')
    parser.add_argument('--start-time', help='sort by start time',
                        dest='sort_key', action='store_const',
                        const='starttime',
                        default='starttime')

    args = parser.parse_args()
    if args.filename:
        fp = open(args.filename, 'rb')
    else:
        fp = sys.stdin

    events = [json.loads(line) for line in fp]
    events.sort(key=lambda e: e[args.sort_key])
    for e in events:
        output_event(e)

if __name__ == '__main__':
    main()
