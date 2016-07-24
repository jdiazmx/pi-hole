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


# DOCOPT


"""Start up Pi-hole's ad-blocking gravity

Usage: pihole gravity"""


# IMPORTS


import pihole_vars
from urllib.parse import urlparse
import requests
from datetime import datetime
import email.utils as eut
from docopt import docopt


# SCRIPT


# Downloads a list
def download_list(ad_list, mod, etag, pihole):
    # Get new list
    r = requests.get(ad_list.get_uri(), timeout=5)

    # Parse domains into list (removes comments)
    domains = [domain.split()[1] for domain in r.text.splitlines() if
               not domain.strip().startswith("#") and len(domain.strip()) > 0]

    pihole.update_list(ad_list.get_uri(), domains, mod, etag)

    print("  * Downloaded!")


# TODO: Add support for locally stored ad-lists
def main(argv):
    docopt(__doc__, argv=argv)

    print("Loading Pi-hole instance...")
    pihole = pihole_vars.Pihole()

    for l in pihole.get_lists():
        # Get domain for output
        domain = '{uri.netloc}'.format(uri=urlparse(l.get_uri()))
        print("Initializing pattern buffer for " + domain + "...")

        # Whitelist ad-list sources, so that we can reach them to update
        pihole.add_whitelist(domain)

        # Get headers
        remote = requests.head(l.get_uri(), timeout=5)

        # Check if the list has been downloaded
        if len(l.get_domains()) == 0:
            # Must be a new list
            print("  * New list, downloading...")

            etag = ""
            last_modified = datetime.now()

            if "ETag" in remote.headers:
                etag = remote.headers["ETag"]
            elif ("Last-Modified" in remote.headers and
                  len(remote.headers["Last-Modified"]) > 0 and
                  remote.headers["Last-Modified"] != '0'):
                last_modified = datetime(*eut.parsedate(remote.headers["Last-Modified"])[:6])

            download_list(l, last_modified, etag, pihole)
        # Check if it needs updating
        else:
            # Check for E-Tag
            if "ETag" in remote.headers:
                etag = remote.headers["ETag"]

                if etag != l.get_etag():
                    print("  * Update found, downloading...")
                    download_list(l, l.get_date(), etag, pihole)
                else:
                    print("  * No update!")
            # Check for Last-Modified header
            elif ("Last-Modified" in remote.headers and
                  len(remote.headers["Last-Modified"]) > 0 and
                  remote.headers["Last-Modified"] != '0'):
                remote_date = datetime(*eut.parsedate(remote.headers["Last-Modified"])[:6])

                # If the remote date is newer than the stored date
                if remote_date > l.get_date():
                    print("  * Update found, downloading...")
                    download_list(l, remote_date, l.get_etag(), pihole)
                else:
                    print("  * No update!")
            else:
                # If we don't know the date, just download it
                print("  * No modification date found, downloading...")
                download_list(l, l.get_date(), l.get_etag(), pihole)

    # Compile domains
    print("Compacting mass... (" + str(len(pihole.get_all_raw_domains())) + " domains)")
    pihole.compile_list()

    # Export domains to hosts file
    print("Generating black hole... (" + str(len(pihole.get_domains())) + " unique domains)")
    pihole.export_hosts()

    # Reload DNS to apply changes
    print("Restarting gravity...")
    pihole_vars.restart_gravity()

    print("Done!")
