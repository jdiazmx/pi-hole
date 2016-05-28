#!/usr/bin/env python3
# Pi-hole: A black hole for Internet advertisements
# (c) 2015, 2016 by Jacob Salmela
# Network-wide ad blocking via your Raspberry Pi
# http://pi-hole.net
# Pi-hole varibles and classes
#
# Pi-hole is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.


# IMPORTS


from datetime import datetime
import sqlite3


# VARIABLES


# URLs of block lists to use
global sources
sources = ["https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
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
pihole_dir = "/etc/" + basename + "/"
ad_list = pihole_dir + "gravity.list"
custom_ad_list = pihole_dir + "ad_list.custom"
list_prefix = "list."
blacklist = pihole_dir + "blacklist.txt"
whitelist = pihole_dir + "whitelist.txt"
domains_extension = "domains"
pihole_ip = "@PIHOLEIP@"

# Variables for various steps of aggregating domains from multiple sources
matter = pihole_dir + basename + ".0.matterandlight.txt"
and_light = pihole_dir + basename + ".1.supernova.txt"
event_horizon = pihole_dir + basename + ".2.eventHorizon.txt"
accretion_disc = pihole_dir + basename + ".3.accretionDisc.txt"

# User-defined custom settings (optional)
local_vars = pihole_dir + "pihole.conf"


# CLASSES


class List:
    def __init__(self, url="", date=datetime.now()):
        self.url = url
        self.date = date


class Query:
    def __init__(self, time=datetime.now(), domain="", client="", record="", blocked=True):
        self.time = time
        self.domain = domain
        self.client = client
        self.record = record
        self.blocked = blocked


class Pihole:
    domains = []
    lists = []
    log = []

    def __init__(self):
        # Read in domains, lists, and log
        database = sqlite3.connect("/etc/pihole/pihole.db")
        cursor = database.cursor()

        # Read in domains
        # ad_domains (domain TEXT)
        cursor.execute("SELECT * FROM ad_domains")
        for row in cursor:
            self.domains.append(row[0])

        # Read in lists
        # lists (url TEXT, date DATETIME)
        cursor.execute("SELECT * FROM lists")
        for row in cursor:
            self.lists.append(List(row[0], row[1]))

        # Read in log
        # log (time DATETIME, domain TEXT, client TEXT, record TEXT, blocked INTEGER)
        for row in cursor:
            self.log.append(Query(row[0], row[1], row[2], row[3], True if row[4] == 1 else False))

        # Close database
        database.close()
