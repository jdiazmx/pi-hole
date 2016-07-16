#!/usr/bin/env python3
# Copyright (c) 2016 Jacob Salmela
# Pi-hole: a DNS based ad-blocker [https://www.pi-hole.net]
#
# Download, aggregate, and parse domain blacklists into one gravity list
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


import pihole_vars
from urllib.parse import urlparse
import requests
from datetime import datetime
import email.utils as eut
from subprocess import check_output, CalledProcessError, call


# SCRIPT


# Downloads a list
def download_list(list, mod, pihole):
    # Clean old list
    list.clean()

    # Get new list
    r = requests.get(list.get_uri(), timeout=5)

    # Parse domains into list (removes comments)
    domains = [domain.split()[1] for domain in r.text.splitlines() if
               not domain.strip().startswith("#") and len(domain.strip()) > 0]

    pihole.update_list(list.get_uri(), domains, mod)

    print("  * Downloaded!")

    return len(domains)


def main():
    print("Loading Pi-hole instance...")
    num_pre_formatted = 0
    pihole = pihole_vars.Pihole()

    # Check for updates
    for l in pihole.lists:
        # Get domain for output
        domain = '{uri.netloc}'.format(uri=urlparse(l.get_uri()))
        print("Initializing pattern buffer for " + domain + "...")

        # Check if the list has been downloaded
        if len(l.get_domains()) == 0:
            # Must be a new list
            print("  * New list, downloading...")
            num_pre_formatted += download_list(l, datetime.now(), pihole)
        # Check if it needs updating
        else:
            # Get request
            remote = requests.head(l.get_uri(), timeout=5)

            # Check for Last-Modified header
            if "Last-Modified" in remote.headers and \
                    len(remote.headers["Last-Modified"]) > 0 and \
                    remote.headers["Last-Modified"] != '0':
                remote_date = datetime(*eut.parsedate(remote.headers["Last-Modified"])[:6])

                # If the remote date is newer than the stored date
                if remote_date > l.get_date():
                    print("  * Update found, downloading...")
                    num_pre_formatted += download_list(l, remote_date, pihole)
                else:
                    print("  * No update!")
                    num_pre_formatted += len(l.get_domains())
                    pass
            else:
                # If we don't know the date, just download it
                print("  * No modification date found, downloading...")
                num_pre_formatted += download_list(l, datetime.now(), pihole)

    # Condense into a formatted list of domains
    print("Formatting " + str(num_pre_formatted) + " domains and removing duplicates...")
    pihole.compile_list()

    # Export domains to hosts file
    print("Exporting " + str(len(pihole.get_domains())) + " domains...")
    pihole.export_hosts()

    # Whitelist adlist uris
    print("Whitelisting x adlist sources...")

    # Whitelist and Blacklist domains
    print("Running whitelist script...")
    print("  * Whitelisted x domains!")
    print("Running blacklist script...")
    print("  * Blacklisted x domains!")

    # Reload dnsmasq to apply changes
    print("Reloading dnsmasq...")
    try:
        pid = int(check_output(["pidof", "-s", "dnsmasq"]))
        call(["killall", "-s", "HUP", "dnsmasq"])
    except CalledProcessError:
        # Must not be running
        call(["service", "dnsmasq", "start"])


if __name__ == "__main__":
    main()
