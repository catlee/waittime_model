#!/usr/bin/env python
"""
Take stream of real job data and turn into a stream of
(requesttime, duration) events
"""
import sys
import json

from utils import output_event


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('filename', help='file to process (default stdin)',
                        nargs='?')
    args = parser.parse_args()

    if args.filename:
        fp = open(args.filename, 'rb')
    else:
        fp = sys.stdin

    for line in fp:
        e = json.loads(line)
        duration = e['endtime'] - e['starttime']
        e = {'requesttime': e['requesttime'], 'duration': duration}
        output_event(e)


if __name__ == '__main__':
    main()
