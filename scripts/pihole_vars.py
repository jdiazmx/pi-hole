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
import os
import socket


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
pihole_ipv6 = "@PIHOLEIPV6@"

# Variables for various steps of aggregating domains from multiple sources
matter = pihole_dir + basename + ".0.matterandlight.txt"
and_light = pihole_dir + basename + ".1.supernova.txt"
event_horizon = pihole_dir + basename + ".2.eventHorizon.txt"
accretion_disc = pihole_dir + basename + ".3.accretionDisc.txt"

# User-defined custom settings (optional)
local_vars = pihole_dir + "pihole.conf"


# CLASSES


# Database Schema:
# ad_domains (domain TEXT)
# unformatted_domains (domain TEXT, list_id INTEGER)
# lists (id INTEGER PRIMARY KEY, uri TEXT, date DATETIME)
# log (time DATETIME, domain TEXT, client TEXT, record TEXT, blocked INTEGER)


time_format = '%Y-%m-%d %H:%M:%S'


def connect():
    return sqlite3.connect("/etc/pihole/pihole.db")


class List:
    def __init__(self, uri="", date=datetime.now()):
        self._uri = uri
        self._date = date
        self._domains = None

    def get_domains(self):
        # Lazy init
        if self._domains is None:
            database = connect()
            cursor = database.cursor()

            # Get domains
            cursor.execute("SELECT domain FROM unformatted_domains WHERE list_id IN (SELECT id FROM lists WHERE uri=?)", (self._uri,))
            self._domains = []
            for row in cursor:
                self._domains.append(row[0])

            database.close()
        return self._domains

    def get_date(self):
        return self._date

    def get_uri(self):
        return self._uri

    def set_domains(self, domains):
        self._domains = domains

    def set_date(self, date):
        self._date = date

    def clean(self):
        database = connect()
        cursor = database.cursor()

        cursor.execute("DELETE FROM unformatted_domains WHERE list_id IN (SELECT id FROM lists WHERE uri=?)", (self._uri,))

        database.commit()
        database.close()


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
        self.reload_domains()
        self.reload_lists()
        self.reload_log()

    def get_domains(self):
        return self.domains

    def get_lists(self):
        return self.lists

    def get_log(self):
        return self.log

    def reload_domains(self):
        database = connect()
        cursor = database.cursor()

        # Read in domains
        cursor.execute("SELECT * FROM ad_domains")
        for row in cursor:
            self.domains.append(row[0])

        database.close()

    def reload_lists(self):
        database = connect()
        cursor = database.cursor()

        # Read in lists
        cursor.execute("SELECT * FROM lists")
        for row in cursor:
            self.lists.append(List(row[1], datetime.strptime(row[2], time_format)))

        database.close()

    def reload_log(self):
        database = connect()
        cursor = database.cursor()

        # Read in log
        cursor.execute("SELECT * FROM log")
        for row in cursor:
            self.log.append(Query(row[0], row[1], row[2], row[3], True if row[4] == 1 else False))

        database.close()

    def update_list(self, uri, domains, time):
        # Update list and clean
        for i in self.lists:
            if i.get_uri() == uri:
                i.set_date(time)
                i.clean()
                i.set_domains(domains)
                break

        database = connect()
        cursor = database.cursor()

        # Get list id
        cursor.execute("SELECT id FROM lists WHERE uri=?", (uri,))
        list_id = cursor.fetchone()[0]

        # Update list time on the database
        cursor.execute("UPDATE lists SET date=? WHERE id=?", (time.strftime(time_format), list_id))

        # Add domains
        for domain in domains:
            cursor.execute("INSERT INTO unformatted_domains VALUES(?, ?)", (domain, list_id))

        database.commit()
        database.close()

    def compile_list(self):
        # Update local domain list
        self.domains = list(set([item for list in self.lists for item in list.get_domains()]))

        database = connect()
        cursor = database.cursor()

        # Clean domains
        cursor.execute("DELETE FROM ad_domains")

        # Insert new domains
        for domain in self.domains:
            cursor.execute("INSERT INTO ad_domains VALUES(?)", (domain,))

        database.commit()
        database.close()

    def export_hosts(self):
        # Check for IPv6
        useIPv6 = os.path.isfile(pihole_dir + ".useIPv6")

        with open(ad_list, 'w') as file:
            # Add pi.hole and hostname first
            file.write(pihole_ip + " pi.hole\n")
            file.write(pihole_ip + " " + socket.gethostname() + "\n")

            # Add the rest of the domains
            for domain in self.domains:
                file.write(pihole_ip + " " + domain + "\n")

                if useIPv6:
                    file.write(pihole_ipv6 + " " + domain + "\n")
