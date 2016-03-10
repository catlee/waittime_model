#!/usr/bin/env python
"""
Calculate the time from build-to-build for machines.
Generally this represents the time to reboot, run runner, etc.
"""
import sys
import json
from collections import defaultdict, namedtuple

Event = namedtuple('Event', 'name, start, end, requested')


def mean(l):
    return sum(l) / len(l)


def percentile(l, p):
    i = int(len(l) * p / 100)
    return sorted(l)[i]


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

    times_per_worker = defaultdict(list)
    for line in fp:
        event = json.loads(line)
        worker_name = event['properties']['slavename']
        starttime = event['starttime']
        endtime = event['endtime']
        requested = event['requesttime']
        e = Event(worker_name, starttime, endtime, requested)
        times_per_worker[worker_name].append(e)

    b2b_per_worker = defaultdict(list)
    b2b_times = []
    for name, times in times_per_worker.items():
        times.sort(key=lambda t: t.start)
        last = None
        for t in times:
            # Discard times where submit time is really close to start time -
            # that means we were waiting for a job
            if abs(t.start - t.requested) < 60:
                #print('skipping', t)
                continue

            if last:
                b2b = t.start - last.end
                if b2b < 0:
                    print('weird:', name)
                else:
                    b2b_per_worker[name].append(b2b)
                    b2b_times.append(b2b)
            last = t

    print('10th percentile b2b:', percentile(b2b_times, 10))
    print('mean b2b:', mean(b2b_times))
    print('median b2b:', percentile(b2b_times, 50))
    print('min b2b:', min(b2b_times))


if __name__ == '__main__':
    main()
