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
from urllib.request import urlopen


# SCRIPT


pihole = Pihole()

# Check for updates
for l in pihole.lists:
    domain = '{uri.netloc}'.format(uri=urlparse(l.uri))
    print("Initializing pattern buffer for " + domain + "...")

    # Check if the list has been downloaded
    domains = l.get_domains()
    if len(domains) == 0:
        # Must be a new list
        pass # Placeholder
    # Check if it needs updating
    else:
        # Check date-modified
        remote_m = urlopen(l.uri, timeout=5).headers["Last-Modified"]
