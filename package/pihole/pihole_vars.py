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
from subprocess import check_output, CalledProcessError, call


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


time_format = '%Y-%m-%d %H:%M:%S'

error_codes = {
    "success": 0,
    "unknown": 1,
    "database_generic": 2,
    "already_exists": 3,
    "does_not_exist": 4,
    "incorrect_params": 5
}


def restart_gravity():
    try:
        pid = int(check_output(["pidof", "-s", "dnsmasq"]))
        call(["killall", "-s", "HUP", "dnsmasq"])
    except CalledProcessError:
        # Must not be running
        call(["service", "dnsmasq", "start"])


def connect():
    return sqlite3.connect(database)


class List:
    def __init__(self, uri="", date=datetime.now(), etag=""):
        self._uri = uri
        self._date = date
        self._domains = None
        self._etag = etag

    def get_domains(self):
        # Lazy init (loading in all the domains of every list every time a new Pihole instance was
        # created would mean a very long wait)
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
        self._time = time
        self._domain = domain
        self._client = client
        self._record = record
        self._blocked = blocked

    def get_time(self):
        return self._time

    def get_domain(self):
        return self._domain

    def get_client(self):
        return self._client

    def get_record_type(self):
        return self._record

    def was_blocked(self):
        return self._blocked


class ListItem:
    def __init__(self, id, domain):
        self._id = id
        self._domain = domain

    def get_id(self):
        return self._id

    def get_domain(self):
        return self._domain


class Pihole:
    _domains = []
    _lists = []
    _whitelist = []
    _blacklist = []
    _log = []

    def __init__(self):
        self.reload_domains()
        self.reload_lists()
        self.reload_whitelist()
        self.reload_blacklist()
        self.reload_log()

    def get_domains(self):
        return self._domains

    def get_all_raw_domains(self):
        return [item for l in self._lists for item in l.get_domains()]

    def get_raw_domains(self):
        return list(set(self.get_all_raw_domains()))

    def get_lists(self):
        return self._lists

    def get_list_uris(self):
        return [l.get_uri() for l in self._lists]

    def get_whitelist(self):
        return [item.get_domain() for item in self._whitelist]

    def get_blacklist(self):
        return [item.get_domain() for item in self._blacklist]

    def get_raw_whitelist(self):
        return self._whitelist

    def get_raw_blacklist(self):
        return self._blacklist

    def get_log(self):
        return self._log

    def reload_domains(self):
        db = connect()
        c = db.cursor()

        # Read in domains
        self._domains = []
        c.execute("SELECT * FROM ad_domains")
        for row in c:
            self._domains.append(row[0])

        db.close()

    def reload_lists(self):
        db = connect()
        c = db.cursor()

        # Read in lists
        self._lists = []
        c.execute("SELECT * FROM lists")
        for row in c:
            self._lists.append(List(row[1], datetime.strptime(row[2], time_format), row[3]))

        db.close()

    def reload_whitelist(self):
        db = connect()
        c = db.cursor()

        # Read in domains
        self._whitelist = []
        c.execute("SELECT * FROM whitelist")
        for row in c:
            self._whitelist.append(ListItem(row[0], row[1]))

        db.close()

    def reload_blacklist(self):
        db = connect()
        c = db.cursor()

        # Read in domains
        self._blacklist = []
        c.execute("SELECT * FROM blacklist")
        for row in c:
            self._blacklist.append(ListItem(row[0], row[1]))

        db.close()

    def reload_log(self):
        db = connect()
        c = db.cursor()

        # Read in log
        self._log = []
        c.execute("SELECT * FROM log")
        for row in c:
            self._log.append(Query(row[0], row[1], row[2], row[3], True if row[4] == 1 else False))

        db.close()

    def update_list(self, uri, domains, time, etag):
        # Update list and clean
        for l in self._lists:
            if l.get_uri() == uri:
                l.set_date(time)
                l.set_etag(etag)
                l.clean()
                l.set_domains(domains)
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

    def add_list(self, uri):
        """
        :return: if the list was added (if it's a new list)
        """
        # Only add if it's a new list
        if uri in self.get_list_uris():
            return False

        l = List(uri)
        self._lists.append(l)

        db = connect()
        c = db.cursor()

        c.execute(
            "INSERT INTO lists (uri, date, etag) VALUES (?, ?, ?)",
            (l.get_uri(), l.get_date().strftime(time_format), l.get_etag())
        )

        db.commit()
        db.close()
        return True

    def add_whitelist(self, domain):
        """
        :return: if the ad list has changed
        """
        # Don't add if it's already there
        if domain in self.get_whitelist():
            return False

        db = connect()
        c = db.cursor()

        c.execute("INSERT INTO whitelist (domain) VALUES (?)", (domain,))
        self._whitelist.append(ListItem(c.lastrowid, domain))

        changed = False

        # Remove from ad domains if it's there
        if domain in self._domains:
            self._domains.remove(domain)
            c.execute("DELETE FROM ad_domains WHERE domain=?", (domain,))
            changed = True

        db.commit()
        db.close()
        return changed

    def add_blacklist(self, domain):
        """
        :return: if the ad list has changed
        """
        # Don't add if it's already there
        if domain in self.get_blacklist():
            return False

        db = connect()
        c = db.cursor()

        c.execute("INSERT INTO blacklist (domain) VALUES (?)", (domain,))
        self._blacklist.append(ListItem(c.lastrowid, domain))

        changed = False

        # Add to list if it's not already there
        if domain not in self._domains:
            self._domains.append(domain)
            c.execute("INSERT INTO ad_domains VALUES (?)", (domain,))
            changed = True

        db.commit()
        db.close()
        return changed

    def remove_list(self, uri):
        """
        :return: if the list was removed (if it was a valid uri)
        """
        # Only remove if it's a valid uri
        if uri not in self.get_list_uris():
            return False

        # Remove list
        self._lists = [l for l in self._lists if l.get_uri() != uri]

        db = connect()
        c = db.cursor()

        c.execute("DELETE FROM lists WHERE uri=?", (uri,))

        db.commit()
        db.close()
        return True

    def remove_whitelist(self, domain):
        """
        :return: if the ad list has changed
        """
        # Only remove if it's there
        if domain not in self.get_whitelist():
            return False

        db = connect()
        c = db.cursor()

        c.execute("DELETE FROM whitelist WHERE domain=?", (domain,))
        self._whitelist = [item for item in self._whitelist if item.get_domain() != domain]

        changed = False

        # Check if domain should be re-added to ad domain list
        if domain in self.get_raw_domains():
            self._domains.append(domain)
            c.execute("INSERT INTO ad_domains VALUES (?)", (domain,))
            changed = True

        db.commit()
        db.close()
        return changed

    def remove_blacklist(self, domain):
        """
        :return: if the ad list has changed
        """
        # Only remove if it's there
        if domain not in self.get_blacklist():
            return False

        db = connect()
        c = db.cursor()

        c.execute("DELETE FROM blacklist WHERE domain=?", (domain,))
        self._blacklist = [item for item in self._blacklist if item.get_domain() != domain]

        changed = False

        # Check if domain should be removed from ad domain list
        if domain not in self.get_raw_domains():
            self._domains.remove(domain)
            c.execute("DELETE FROM ad_domains WHERE domain=?", (domain,))
            changed = True

        db.commit()
        db.close()
        return changed

    def compile_list(self):
        # Load all domains from lists (also removes duplicates)
        self._domains = self.get_raw_domains()

        # Remove whitelisted entries
        self._domains = [item for item in self._domains if item not in self.get_whitelist()]

        # Add blacklisted entries (if not already blocked)
        self._domains = list(set().union(self._domains, self.get_blacklist()))

        db = connect()
        c = db.cursor()

        # Clean domains
        c.execute("DELETE FROM ad_domains")

        # Insert new domains
        for domain in self._domains:
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
            for domain in self._domains:
                file.write(pihole_ip + " " + domain + "\n")

                if useIPv6:
                    file.write(pihole_ipv6 + " " + domain + "\n")
