#!/usr/bin/env python3
"""Very crude news feed alarm. Not a feed parser"""

import argparse
import datetime
import json
import os
import sys
from urllib.error import URLError
from xml.sax import SAXParseException
from zoneinfo import ZoneInfo
import feedparser
from prettytable import PrettyTable

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

    # The Last-Modified field of the feed uses GMT. Use also
    # GMT TZ for our own dates, even they are are decorrelated
    # from the Last-Modified field
    now = datetime.datetime.now(tz=ZoneInfo("GMT"))

    # Feed is gone, or we did not provide a URL
    if not "url" in f_cfg or f_cfg.get("status", "") == "410":
        return f_cfg

    if "last_checked" in f_cfg:
        last_checked = datetime.datetime.strptime(
            f_cfg["last_checked"], "%a, %d %b %Y %H:%M:%S %Z"
        )
        last_checked = last_checked.replace(tzinfo=ZoneInfo("GMT"))
        # No need to poll more than once a day
        if (now - last_checked).days < 1:
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
        f_cfg["status"] = d.status
    elif d.bozo and isinstance(d.bozo_exception, (URLError, SAXParseException)):
        f_cfg["status"] = -1  # Bad URL / Bad feed
    else:
        f_cfg["status"] = -2  # What is this ?

    f_cfg["last_checked"] = now.strftime("%a, %d %b %Y %H:%M:%S %Z")
    cfg[feed_name] = f_cfg
    return f_cfg


def extract_date(dte):
    """Extract datestring from datetime"""
    return datetime.datetime.strptime(dte, "%a, %d %b %Y %H:%M:%S %Z").strftime(
        "%Y-%m-%d"
    )


def display_feeds(feeds):
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
    table = PrettyTable()
    table.field_names = [
        "Feed",
        "Status code",
        "Status",
        "Last modified",
        "Last checked",
    ]

    for feed_name, f_cfg in feeds:
        modded, checked = "-", "-"
        if "modified" in f_cfg:
            modded = extract_date(f_cfg["modified"])
        if "last_checked" in f_cfg:
            checked = extract_date(f_cfg["last_checked"])
        table.add_row(
            [
                feed_name,
                f_cfg["status"],
                status_map.get(f_cfg["status"], "Unknown"),
                modded,
                checked,
            ]
        )
    print(table)


def display_feeds_short(res_array):
    """Gather basic stats and display them"""
    (modified, bad) = (0, 0)
    sts_a = [_[1] for _ in res_array]
    for sts in sts_a:
        status = sts.get("status")
        if status in (200, 301):
            modified += 1
        elif status in (404, 410, 429, -1, -2):
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
        feed_cfg = handle_feed(feed, CFG, ARGS)
        results.append((feed, feed_cfg))
if ARGS.short:
    display_feeds_short(results)
else:
    display_feeds(results)

write_config(ARGS.config, CFG)  # Let's hope we did not crash in between
