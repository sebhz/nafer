#!/usr/bin/env python3
"""Very crude news feed alarm. Not a feed parser"""

import argparse
import json
import os
import sys
from urllib.error import URLError
import feedparser

CONFIG_DEFAULT = os.path.join(f"{os.environ['HOME']}", ".nafer")


def read_config(config_name):
    """Get JSON config dict"""
    with open(config_name, encoding="utf-8") as f:
        d = json.load(f)
    return d


def write_config(config_name, config):
    """Write back JSON config dict"""
    with open(config_name, "w", encoding="utf-8") as f:
        f.write(json.dumps(config, indent=2))


def parse_args():
    """Basic argument parser"""
    parser = argparse.ArgumentParser(description="News feed basic alarm")
    parser.add_argument("--short", help="short output", action="store_true")
    parser.add_argument(
        "--config", help="configuration file", default=CONFIG_DEFAULT, type=str
    )
    parser.add_argument("--list", help="list feeds", action="store_true")
    parser.add_argument(
        "feeds",
        nargs="*",
        help="feeds to check. Optional. If not provided checks all feeds",
    )
    _args = parser.parse_args()
    return _args


def handle_feed(feed_name, cfg):
    """Check feed and status"""
    f_cfg = cfg[feed_name]
    if not "url" in f_cfg:
        return 410  # Return "gone"
    kwargs = {}
    for option in ("modified", "etag"):
        if f_cfg.get(option) is not None:
            kwargs[option] = f_cfg.get(option)
    if kwargs:
        d = feedparser.parse(f_cfg["url"], **kwargs)
    else:
        d = feedparser.parse(f_cfg["url"])
    if d.bozo and isinstance(d.bozo_exception, URLError):
        return -1  # Bad URL
    if "modified" in d:
        f_cfg["modified"] = d.modified
    if "etag" in d:
        f_cfg["etag"] = d.etag
    if d.status == 301:  # Permanent redirect - update URL
        if "href" in d:
            f_cfg["url"] = d.href
    if d.status == 410:  # Feed is gone - delete URL
        f_cfg.pop("url", None)
    cfg[feed_name] = f_cfg
    return d.status


def display_status(feed_name, sts):
    """Display feed status"""
    status_map = {
        200: "Feed updated",
        301: "Feed permanently redirected",
        304: "Feed not modified",
        404: "Feed not found",
        410: "Feed gone",
        429: "Too many requests",
        -1: "Bad feed URL",
    }
    print(f"{feed_name}: {status_map.get(sts, 'Unknown')} ({sts})")


def display_short_status(res_array):
    """Gather basic stats and display them"""
    (modified, bad) = (0, 0)
    sts_a = [_[1] for _ in res_array]
    for sts in sts_a:
        if sts in (200, 301):
            modified += 1
        elif sts in (404, 410, 429, -1):
            bad += 1
    print(f"{modified}/{bad}!/{len(res_array)}")


ARGS = parse_args()
CFG = read_config(ARGS.config)

if ARGS.list:
    for feed_cfg in CFG:
        print(f"{feed_cfg}: {CFG[feed_cfg]['url']}")
    sys.exit(0)

results = []
for feed in CFG:
    if ARGS.feeds == [] or feed in ARGS.feeds:
        status = handle_feed(feed, CFG)
        results.append((feed, status))
if ARGS.short:
    display_short_status(results)
else:
    for feed, status in results:
        display_status(feed, status)
write_config(ARGS.config, CFG)  # Let's hope we did not crash in between
