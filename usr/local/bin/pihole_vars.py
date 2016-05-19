#!/usr/bin/env python
# Pi-hole: A black hole for Internet advertisements
# (c) 2015, 2016 by Jacob Salmela
# Network-wide ad blocking via your Raspberry Pi
# http://pi-hole.net
# Pi-hole varibles
#
# Pi-hole is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.

##############################
######### IMPORTS ############

##############################
######## VARIABLES ###########
# URLs of block lists to use
global sources
sources=["https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
"http://adblock.gjtech.net/?format=unix-hosts",
"http://mirror1.malwaredomains.com/files/justdomains",
"http://sysctl.org/cameleon/hosts",
"https://zeustracker.abuse.ch/blocklist.php?download=domainblocklist",
"https://s3.amazonaws.com/lists.disconnect.me/simple_tracking.txt",
"https://s3.amazonaws.com/lists.disconnect.me/simple_ad.txt",
"http://hosts-file.net/ad_servers.txt"]

global basename, pihole_dir, ad_list, custom_ad_list, list_prefix, blacklist, whitelist, domains_extension, matter, and_light, event_horizon, accretion_disc, local_vars

# File path variables
basename = "pihole"
pihole_dir = "/etc/" + basename
ad_list = pihole_dir + "/gravity.list"
custom_ad_list = pihole_dir + "/ad_list.custom"
list_prefix = "list."
blacklist = pihole_dir + "/blacklist.txt"
whitelist = pihole_dir + "/whitelist.txt"
domains_extension = "domains"

# Variables for various steps of aggregating domains from multiple sources
matter = basename + ".0.matterandlight.txt"
and_light = basename + ".1.supernova.txt"
event_horizon = basename + ".2.eventHorizon.txt"
accretion_disc = basename + ".3.accretionDisc.txt"

# User-defined custom settings (optional)
local_vars = pihole_dir + "/pihole.conf"

##############################
######## FUNCTIONS ###########
