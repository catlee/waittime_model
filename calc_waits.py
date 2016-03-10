#!/usr/bin/env python
"""
Calculate the wait times given real job data
"""
import sys
import json


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

    wait_times = []
    for line in fp:
        event = json.loads(line)
        wait = event['starttime'] - event['requesttime']
        wait_times.append(wait)

    # Print report
    t = len(wait_times)
    for x in range(0, 3600, 900):
        # How many jobs do we have with wait time > x < x + 900
        from_ = x
        to_ = x + 900
        n = len([w for w in wait_times if (w >= from_ and w < to_)])
        p = 100 * n / t
        print('%s - %s: %s (%.2f%%)' % (from_/60, to_/60, n, p))
    # How many are waiting longer
    from_ = 3600
    n = len([w for w in wait_times if w > from_])
    p = 100 * n / t
    print('%s+      : %s (%.2f%%)' % (from_/60, n, p))
    print('Total wait: %i hours' % (sum(wait_times)/3600))


if __name__ == '__main__':
    main()
