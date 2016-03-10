#!/usr/bin/env python
"""
Fetches build data from builddata.pub.build.mozilla.org and outputs it to stdout.
One line of output corresponds to one build/test event.
Output is generally sorted in order of start time, but not guaranteed to be.
"""
import os
from datetime import datetime, date, timedelta
from argparse import ArgumentTypeError, ArgumentParser
import gzip
import json

import asyncio
import aiohttp

from utils import output_event

import logging
log = logging.getLogger(__name__)

BASE_URL = 'http://builddata.pub.build.mozilla.org/builddata/buildjson'
ONE_DAY = timedelta(days=1)


def get_url(d):
    return "{}/builds-{:%Y-%m-%d}.js.gz".format(BASE_URL, d)


def get_dates(from_date, to_date):
    d = from_date
    while d <= to_date:
        yield d
        d += ONE_DAY


def cache_filename(d, cache_dir):
    return os.path.join(cache_dir, d.strftime('%Y-%m-%d.js.gz'))


def is_cached(d, cache_dir):
    filename = cache_filename(d, cache_dir)
    return os.path.exists(filename)


def date_argument(string):
    try:
        d = datetime.strptime(string, '%Y-%m-%d')
        return d.date()
    except ValueError:
        raise ArgumentTypeError(
            "%r is not a string in YYYY-MM-DD format" % string)


async def download_url(url, dest):
    log.info('fetching %s to %s', url, dest)
    async with aiohttp.get(url) as resp:
        if resp.status != 200:
            log.warning(
                'could not fetch %s: %s %s',
                url, resp.status, resp.reason,
            )
            return

        tmpfile = dest + '.tmp'
        with gzip.GzipFile(tmpfile, 'wb') as fp:
            while True:
                chunk = await resp.content.read(1024)
                if not chunk:
                    break
                fp.write(chunk)
        os.rename(tmpfile, dest)


def parse_buildjson(filename):
    log.info('parsing %s', filename)
    with gzip.open(filename) as fp:
        data = json.loads(fp.read().decode('ascii'))
        for b in data['builds']:
            yield b


async def main(loop):
    parser = ArgumentParser()
    today = date.today()
    yesterday = today - ONE_DAY
    parser.add_argument('--cache-dir', dest='cache_dir', default='cache',
                        help='directory to store cached files in')
    parser.add_argument('--from', dest='from_date', type=date_argument,
                        help='first date (YYYY-MM-DD) to fetch data for',
                        default=yesterday,)
    parser.add_argument('--to', dest='to_date', type=date_argument,
                        help='last date (YYYY-MM-DD) to fetch data for',
                        default=today,)
    parser.add_argument('--ignore-cache', dest='ignore_cache', default=False,
                        action='store_true', help='ignore cached data')
    parser.add_argument('-q', '--quiet', dest='loglevel', action='store_const',
                        const=logging.WARNING, help='less output',
                        default=logging.INFO,)
    parser.add_argument('-v', '--verbose', dest='loglevel',
                        action='store_const', const=logging.DEBUG,
                        help='more output')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel, format='%(asctime)s %(message)s')

    # Procedural glue
    # Make sure cache_dir exists
    if not os.path.exists(args.cache_dir):
        os.makedirs(args.cache_dir)

    dates = get_dates(args.from_date, args.to_date)

    for d in dates:
        filename = cache_filename(d, args.cache_dir)
        if args.ignore_cache or not is_cached(d, args.cache_dir):
            url = get_url(d)
            await download_url(url, filename)
        # Read the file and output event lines
        for event in parse_buildjson(filename):
            output_event(event)

    exit()

    if not args.ignore_cache:
        needs_download = [d for d in dates if not is_cached(d, args.cache_dir)]
    else:
        needs_download = dates

    urls = [(d, get_url(d)) for d in needs_download]

    # Download up to 3 at a time
    j = 3
    downloading = []
    to_download = [(url, cache_filename(d, args.cache_dir)) for (d, url) in urls]
    while to_download:
        while len(downloading) < j and to_download:
            url, filename = to_download.pop(0)
            t = asyncio.ensure_future(download_url(url, filename))
            downloading.append(t)
        done, pending = await asyncio.wait(downloading, return_when=asyncio.FIRST_COMPLETED)
        for t in done:
            downloading.remove(t)
    # Wait for the rest
    log.debug('no more files to download; waiting for in-progress downloads')
    if downloading:
        await asyncio.wait(downloading)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
