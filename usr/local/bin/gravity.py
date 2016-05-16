#!/usr/bin/python
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

##############################
######### IMPORTS ############
import pihole_vars
import urllib
import os.path
from urlparse import urlparse

##############################
######## FUNCTIONS ###########
def local_calibration():
    if os.path.isfile(pihole_conf):
        print("Local calibration requested.  Sanning...")

# Downloads the blocklists
def gravity_well():
    # For each URL in the sources list
    for idx, url in enumerate(pihole_vars.sources):
        # Get just the domain name so it can be displayed to the user
        parsed_uri = urlparse(url)
        domain = '{uri.netloc}'.format(uri=parsed_uri)
        print("Initiating transport of " + domain + "...")

        # Save the file as list.n.domain.name.domains
        # This is useful for debugging as well as keeping the lists out of RAM
        blocklist = urllib.URLopener()
        blocklist.retrieve(url, "list." + str(idx) + "." + domain + domains_extension)







# Download the blocklists
gravity_well()
