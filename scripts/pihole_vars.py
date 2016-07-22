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


# VARIABLES


# URLs of block lists to use
sources = ["https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",  # ETag
           "http://adblock.gjtech.net/?format=unix-hosts",  # Last-Modified
           "http://mirror1.malwaredomains.com/files/justdomains",  # ETag + Last-Modified
           "http://sysctl.org/cameleon/hosts",  # ETag + Last-Modified
           "https://zeustracker.abuse.ch/blocklist.php?download=domainblocklist",  # Last-Modified
           "https://s3.amazonaws.com/lists.disconnect.me/simple_tracking.txt",  # ETag + Last-Modified
           "https://s3.amazonaws.com/lists.disconnect.me/simple_ad.txt",  # ETag + Last-Modified
           "https://hosts-file.net/ad_servers.txt"]  # ETag + Last-Modified

# File path variables
basename = "pihole"
pihole_dir = "/etc/" + basename + "/"
version = "Pi-hole 3.0.0"
database = pihole_dir + "pihole.db"
ad_list = pihole_dir + "gravity.list"
custom_ad_list = pihole_dir + "ad_list.custom"
blacklist_path = pihole_dir + "blacklist.txt"
whitelist_path = pihole_dir + "whitelist.txt"
pihole_ip = "@PIHOLEIP@"
pihole_ipv6 = "@PIHOLEIPV6@"

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
    return sqlite3.connect(database)


class List:
    def __init__(self, uri="", date=datetime.now(), etag=""):
        self._uri = uri
        self._date = date
        self._domains = None
        self._etag = etag

    def get_domains(self):
        # Lazy init
        if self._domains is None:
            db = connect()
            c = db.cursor()

            # Get domains
            c.execute(
                "SELECT domain FROM unformatted_domains WHERE list_id IN (SELECT id FROM lists WHERE uri=?)",
                (self._uri,)
            )
            self._domains = []
            for row in c:
                self._domains.append(row[0])

            db.close()
        return self._domains

    def get_date(self):
        return self._date

    def get_uri(self):
        return self._uri

    def get_etag(self):
        return self._etag

    def set_domains(self, domains):
        self._domains = domains

    def set_date(self, date):
        self._date = date

    def set_etag(self, etag):
        self._etag = etag

    def clean(self):
        db = connect()
        c = db.cursor()

        c.execute(
            "DELETE FROM unformatted_domains WHERE list_id IN (SELECT id FROM lists WHERE uri=?)",
            (self._uri,)
        )

        db.commit()
        db.close()


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
    whitelist = []
    blacklist = []
    log = []

    def __init__(self):
        self.reload_domains()
        self.reload_lists()
        self.reload_log()

    def get_domains(self):
        return self.domains

    def get_lists(self):
        return self.lists

    def get_whitelist(self):
        return self.whitelist

    def get_blacklist(self):
        return self.blacklist

    def get_log(self):
        return self.log

    def reload_domains(self):
        db = connect()
        c = db.cursor()

        # Read in domains
        c.execute("SELECT * FROM ad_domains")
        for row in c:
            self.domains.append(row[0])

        db.close()

    def reload_lists(self):
        db = connect()
        c = db.cursor()

        # Read in lists
        c.execute("SELECT * FROM lists")
        for row in c:
            self.lists.append(List(row[1], datetime.strptime(row[2], time_format), row[3]))

        db.close()

    def reload_whitelist(self):
        db = connect()
        c = db.cursor()

        # Read in domains
        c.execute("SELECT * FROM whitelist")
        for row in c:
            self.whitelist.append(row[0])

        db.close()

    def reload_blacklist(self):
        db = connect()
        c = db.cursor()

        # Read in domains
        c.execute("SELECT * FROM blacklist")
        for row in c:
            self.blacklist.append(row[0])

        db.close()

    def reload_log(self):
        db = connect()
        c = db.cursor()

        # Read in log
        c.execute("SELECT * FROM log")
        for row in c:
            self.log.append(Query(row[0], row[1], row[2], row[3], True if row[4] == 1 else False))

        db.close()

    def update_list(self, uri, domains, time, etag):
        # Update list and clean
        for i in self.lists:
            if i.get_uri() == uri:
                i.set_date(time)
                i.set_etag(etag)
                i.clean()
                i.set_domains(domains)
                break

        db = connect()
        c = db.cursor()

        # Get list id
        c.execute("SELECT id FROM lists WHERE uri=?", (uri,))
        list_id = c.fetchone()[0]

        # Update list time on the database
        c.execute(
            "UPDATE lists SET date=?, etag=? WHERE id=?",
            (time.strftime(time_format), etag, list_id)
        )

        # Add domains
        for domain in domains:
            c.execute("INSERT INTO unformatted_domains VALUES(?, ?)", (domain, list_id))

        db.commit()
        db.close()

    def add_whitelist(self, domain):
        # Don't add if it's already there
        if domain in self.whitelist:
            return

        self.whitelist.append(domain)

        db = connect()
        c = db.cursor()

        c.execute("INSERT INTO whitelist VALUES (?)", (domain,))

        db.commit()
        db.close()

    def add_blacklist(self, domain):
        # Don't add if it's already there
        if domain in self.blacklist:
            return

        self.blacklist.append(domain)

        db = connect()
        c = db.cursor()

        c.execute("INSERT INTO blacklist VALUES (?)", (domain,))

        db.commit()
        db.close()

    def remove_whitelist(self, domain):
        # Only remove if it's there
        if domain not in self.whitelist:
            return

        self.whitelist.remove(domain)

        db = connect()
        c = db.cursor()

        c.execute("DELETE FROM whitelist WHERE domain=?", (domain,))

        db.commit()
        db.close()

    def remove_blacklist(self, domain):
        # Only remove if it's there
        if domain not in self.blacklist:
            return

        self.blacklist.remove(domain)

        db = connect()
        c = db.cursor()

        c.execute("DELETE FROM blacklist WHERE domain=?", (domain,))

        db.commit()
        db.close()

    def compile_list(self):
        # Update local domain list
        self.domains = list(set([item for l in self.lists for item in l.get_domains()]))

        db = connect()
        c = db.cursor()

        # Clean domains
        c.execute("DELETE FROM ad_domains")

        # Insert new domains
        for domain in self.domains:
            c.execute("INSERT INTO ad_domains VALUES(?)", (domain,))

        db.commit()
        db.close()

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
