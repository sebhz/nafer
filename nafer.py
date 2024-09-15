#!/usr/bin/env python3
"""Very crude news feed alarm. Not a feed parser"""

import argparse
import json
import os
import sys
from urllib.error import URLError
from xml.sax import SAXParseException
from datetime import datetime
import feedparser

CONFIG_DEFAULT = os.path.join(f"{os.environ['HOME']}", ".nafer")


def read_config(config_name):
    """Get JSON config dict"""
    try:
        with open(config_name, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        d = None
    return d


def write_config(config_name, config):
    """Write back JSON config dict"""
    with open(config_name, "w", encoding="utf-8") as f:
        f.write(json.dumps(config, indent=2))


def parse_args():
    """Basic argument parser"""
    parser = argparse.ArgumentParser(description="News feed basic alarm")
    parser.add_argument(
        "-d", "--debug", help="enable debug output", action="store_true"
    )
    parser.add_argument("-s", "--short", help="short output", action="store_true")
    parser.add_argument(
        "-c", "--config", help="configuration file", default=CONFIG_DEFAULT, type=str
    )
    parser.add_argument("--list", help="list feeds", action="store_true")
    parser.add_argument(
        "-u",
        "--uncached",
        help="retrieve state. Do not used cached info",
        action="store_true",
    )
    parser.add_argument(
        "feeds",
        nargs="*",
        help="feeds to check. Optional. If not provided checks all feeds",
    )
    _args = parser.parse_args()
    return _args


def handle_feed(feed_name, cfg, args):
    """Check feed and status"""
    options_checked = ("modified", "etag")
    f_cfg = cfg[feed_name]
    if "cached" in f_cfg and not args.uncached:
        return f_cfg
    if not "url" in f_cfg:
        f_cfg["cached"] = 410  # "gone" - nothing to try and retrieve
        cfg[feed_name] = f_cfg
        return f_cfg
    kwargs = {}
    for option in options_checked:
        if f_cfg.get(option) is not None:
            kwargs[option] = f_cfg.get(option)

    d = feedparser.parse(f_cfg["url"], **kwargs)

    if args.debug:
        print(d, file=sys.stderr)
    if "status" in d:
        for option in options_checked:
            if option in d:
                f_cfg[option] = getattr(d, option)
        if d.status == 301:  # Permanent redirect - update URL
            if "href" in d:
                f_cfg["url"] = d.href
        if d.status == 410:  # Feed is gone - delete URL
            f_cfg.pop("url", None)
        f_cfg["cached"] = d.status
    elif d.bozo and isinstance(d.bozo_exception, (URLError, SAXParseException)):
        f_cfg["cached"] = -1  # Bad URL / Bad feed
    else:
        f_cfg["cached"] = -2  # What is this ?

    cfg[feed_name] = f_cfg
    return f_cfg


def display_feed(feed_name, f_cfg):
    """Display feed status"""
    status_map = {
        200: "Feed updated",
        301: "Feed permanently redirected",
        304: "Feed not modified",
        404: "Feed not found",
        410: "Feed gone",
        429: "Too many requests",
        -1: "Bad feed/URL",
        -2: "Unknown",
    }
    sys.stdout.write(
        f"{feed_name}: {status_map.get(f_cfg['cached'], 'Unknown')} ({f_cfg['cached']})"
    )
    if "modified" in f_cfg:
        sys.stdout.write(
            f" ({datetime.strptime(f_cfg['modified'], '%a, %d %b %Y %H:%M:%S %Z').strftime('%Y-%m-%d')})"
        )
    print("")


def display_feed_short(res_array):
    """Gather basic stats and display them"""
    (modified, bad) = (0, 0)
    sts_a = [_[1] for _ in res_array]
    for sts in sts_a:
        cached = sts.get("cached")
        if cached in (200, 301):
            modified += 1
        elif cached in (404, 410, 429, -1, -2):
            bad += 1
    print(f"{modified}/{bad}!/{len(res_array)}")


ARGS = parse_args()
CFG = read_config(ARGS.config)
if CFG is None:
    if ARGS.short:
        print("x/x!/x")
    else:
        print("Issue with the configuration file. Exiting.", file=sys.stderr)
    sys.exit(-1)

if ARGS.list:
    for feed_cfg in CFG:
        print(f"{feed_cfg}: {CFG[feed_cfg]['url']}")
    sys.exit(0)

results = []
for feed in CFG:
    if ARGS.feeds == [] or feed in ARGS.feeds:
        status = handle_feed(feed, CFG, ARGS)
        results.append((feed, status))
if ARGS.short:
    display_feed_short(results)
else:
    for feed, feed_cfg in results:
        display_feed(feed, feed_cfg)
write_config(ARGS.config, CFG)  # Let's hope we did not crash in between
