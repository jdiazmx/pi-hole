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

pihole = pihole_vars.Pihole()


# Downloads a list
def download_list(list):
    print(" Downloaded!")


# Check for updates
for l in pihole.lists:
    # Get domain for output
    domain = '{uri.netloc}'.format(uri=urlparse(l.uri))
    print("Initializing pattern buffer for " + domain + "...", end="")

    # Check if the list has been downloaded
    domains = l.get_domains()
    if len(domains) == 0:
        # Must be a new list
        print(" New list, downloading...", end="")
        download_list(l)
    # Check if it needs updating
    else:
        # Get request
        remote = requests.head(l.uri, timeout=5)

        # Check for Last-Modified header
        if "Last-Modified" in remote.headers and len(remote.headers["Last-Modified"]) > 0:
            remote_date = datetime(*eut.parsedate(remote.headers["Last-Modified"])[:6])

            # If the remote date is newer than the stored date
            if remote_date > l.get_date():
                print(" Update found, downloading...", end="")
                download_list(l)
            else:
                print(" No update!")
                pass
        else:
            # If we don't know the date, just download it
            print(" No modification date found, downloading...", end="")
            download_list(l)

