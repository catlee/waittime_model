#!/usr/bin/env python
"""
Take a stream of (requesttime, duration) events and figure out wait times
for a given pool size
"""
import sys
import json
import bisect


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('filename', help='file to process (default stdin)',
                        nargs='?')
    parser.add_argument('-n', '--size',
                        help='how many machines to simulate', dest='size',
                        type=int,
                        required=True,
                        )
    parser.add_argument('-b', '--b2b', type=int, help='time between jobs',
                        dest='b2b',
                        required=True)
    args = parser.parse_args()

    if args.filename:
        fp = open(args.filename, 'rb')
    else:
        fp = sys.stdin

    available_machines = list(range(args.size))
    busy_machines = []
    pending = []

    events = sorted((json.loads(line) for line in fp), key=lambda e: e['requesttime'])
    events = [(e['requesttime'], 'request', e['duration']) for e in events]

    wait_times = []

    while events:
        e = events.pop(0)
        t, type_, *event_data = e
        if type_ == 'request':
            # If we have a free machine, use it
            duration = e[-1]
            if available_machines:
                m = available_machines.pop(0)
                # Schedule the machine to be back in duration + b2b time
                finish = (t + duration + args.b2b, 'finish', m)
                bisect.insort_left(events, finish)
                # Record our wait time
                wait_times.append(0)
            else:
                pending.append(e)

        elif type_ == 'finish':
            # A machine just freed up, check if we have pending
            m = e[-1]
            if pending:
                j = pending.pop(0)
                duration = j[-1]
                # Schedule the machine to be back in duration + b2b time
                finish = (t + duration + args.b2b, 'finish', m)
                bisect.insort_left(events, finish)
                # Record our wait time
                wait_times.append(t - j[0])
            else:
                # Put the machine back in the pool
                available_machines.append(m)

        else:
            print('unsupported event!', e)

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
