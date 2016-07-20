#!/usr/bin/env python3
# Copyright (c) 2016 Jacob Salmela
# Pi-hole: a DNS based ad-blocker [https://www.pi-hole.net]
#
# Pi-hole variables and classes
#
# The Pi-Hole is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


# IMPORTS


from datetime import datetime
import sqlite3
import os
import socket
import argparse


# VARIABLES


# URLs of block lists to use
global sources
sources = ["https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",  # ETag
           "http://adblock.gjtech.net/?format=unix-hosts",  # Last-Modified
           "http://mirror1.malwaredomains.com/files/justdomains",  # ETag + Last-Modified
           "http://sysctl.org/cameleon/hosts",  # ETag + Last-Modified
           "https://zeustracker.abuse.ch/blocklist.php?download=domainblocklist",  # Last-Modified
           "https://s3.amazonaws.com/lists.disconnect.me/simple_tracking.txt",  # ETag + Last-Modified
           "https://s3.amazonaws.com/lists.disconnect.me/simple_ad.txt",  # ETag + Last-Modified
           "https://hosts-file.net/ad_servers.txt"]  # ETag + Last-Modified

global basename, pihole_dir, version, ad_list, custom_ad_list, blacklist, whitelist, pihole_ip, pihole_ipv6, local_vars

# File path variables
basename = "pihole"
pihole_dir = "/etc/" + basename + "/"
version = "Pi-hole 3.0.0"
database = pihole_dir + "pihole.db"
ad_list = pihole_dir + "gravity.list"
custom_ad_list = pihole_dir + "ad_list.custom"
blacklist = pihole_dir + "blacklist.txt"
whitelist = pihole_dir + "whitelist.txt"
pihole_ip = "@PIHOLEIP@"
pihole_ipv6 = "@PIHOLEIPV6@"

# User-defined custom settings (optional)
local_vars = pihole_dir + "pihole.conf"


# CLASSES


# Credit for this class: http://stackoverflow.com/a/31124505
class CustomHelpFormatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
        if not action.option_strings or action.nargs == 0:
            return super()._format_action_invocation(action)
        default = self._get_default_metavar_for_optional(action)
        args_string = self._format_args(action, default)
        return ', '.join(action.option_strings) + ' ' + args_string


# Database Schema:
# ad_domains (domain TEXT)
# unformatted_domains (domain TEXT, list_id INTEGER)
# lists (id INTEGER PRIMARY KEY, uri TEXT, date DATETIME)
# log (time DATETIME, domain TEXT, client TEXT, record TEXT, blocked INTEGER)


time_format = '%Y-%m-%d %H:%M:%S'


def connect():
    return sqlite3.connect(database)


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
        hostname = socket.gethostname()

        with open(ad_list, 'w') as file:
            # Add pi.hole and hostname first
            file.write(pihole_ip + " pi.hole\n")
            file.write(pihole_ip + " " + hostname + "\n")

            if useIPv6:
                file.write(pihole_ipv6 + " pi.hole\n")
                file.write(pihole_ipv6 + " " + hostname + "\n")

            # Add the rest of the domains
            for domain in self.domains:
                file.write(pihole_ip + " " + domain + "\n")

                if useIPv6:
                    file.write(pihole_ipv6 + " " + domain + "\n")
