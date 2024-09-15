# Not a feed reader

## Synopsis

Checks for RSS feed to see if new articles popped up since
last time checked. Just fire it up in a statusbar at startup
and update it every day.

Configuration and feed state stored in the same file on disk.

A one day cooldown is implemented. If trying to get the status more often, the server is not polled, but the latest status is returned.

## Arguments

    * --config <config_file>: use <config_file> as a configuration/state. Default is to use ${HOME}/.nfwba.
    * --debug: display the content of the server response. Useful for debug.
    * --list: list all feed names in the configuration/state file.
    * --short: short listing, for usage in a statusbar. Just outputs x/y!/z, with x the number of updated feeds, and y numbers of bad feeds and z the total number of feeds.

If invoked with only a feed name, display the status of the feed.
If invoked without arguments, display the status of all feeds.

## Config file

JSON. See the sample config.
