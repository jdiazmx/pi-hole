#!/usr/bin/env python3
# Pi-hole: A black hole for Internet advertisements
# (c) 2015, 2016 by Jacob Salmela
# Network-wide ad blocking via your Raspberry Pi
# http://pi-hole.net
# Pi-hole gravity function to download, aggregate, and parse source lists
#
# Pi-hole is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.


# IMPORTS


import pihole_vars
from urllib.parse import urlparse
import requests
from datetime import datetime
import email.utils as eut


# SCRIPT


# Downloads a list
def download_list(list, mod, pihole):
    # Clean old list
    list.clean()

    # Get new list
    r = requests.get(list.get_uri(), timeout=5)

    # Parse domains into list (removes comments)
    domains = [domain.split(" ")[1] for domain in r.text.splitlines() if
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


if __name__ == "__main__":
    main()
