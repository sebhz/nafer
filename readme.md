# Not a feed reader

## Synopsis

Checks for RSS feed to see if new articles popped up since
last time checked. Just fire it up in a statusbar at startup
and update it every 8 hours or so (or never).

Configuration and feed state stored in the same file on disk.

Does not know when or even if the articles were read. Just checks
if there is something new since last time. If not, it will not report anything.

## Arguments

    * --config <config_file>: use <config_file> as a configuration/state. Default is to use ${HOME}/.nfwba.
    * --list: list all feed names in the configuration/state file.
    * --short: short listing, for usage in a statusbar. Just outputs x/y!/z, with x the number of updated feeds, and y the numbers of bad feeds and z the total number of feeds.

If invoked with only a feed name, display the status of the feed.
If invoked without arguments, display the status of all feeds.

## Config file

JSON. See the sample config.
