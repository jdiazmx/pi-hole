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
import urllib2
import os
import time
import datetime
from urlparse import urlparse

##############################
######## FUNCTIONS ###########
def local_calibration():
    if os.path.isfile(pihole_conf):
        print("Local calibration requested.  Sanning...")

# Be a respectful netizen by only downloading the list if it is newer than the local file
def transport_buffer(url, filename):
    # Get the headers of the URL so the mtime can be extracted for comparision with the local file
    u = urllib2.urlopen(url)
    remote_mtime = u.info().getdate("Last-Modified")
    if remote_mtime == None:
        pass
    else:
        if os.path.isfile(filename):
            # Format the time tuple to match the format of the mtime gathered from the local file
            remote_mtime = time.strftime("%a %h %d %H:%M:%S %Y", remote_mtime)
            local_mtime = time.ctime(os.path.getmtime(filename))
            print("  * Existing list detected.   (" + local_mtime + ")")

            # Compare the local mtime to the remote mtime.  <------THIS IS BROKEN STILL, but the functionality is there
            # If they are the same, set to False so the list will not be downloaded in grvity_well
            # Since the content is the same, there is no need to re-download it
            if local_mtime == remote_mtime:
                print("  * No changes detected.")
                return False
            else:
                print("  * Remote list is newer.     (" + remote_mtime + ")")
                return True

# Downloads the blocklists
def gravity_well():
    # For each URL in the sources list
    for idx, url in enumerate(pihole_vars.sources):
        # Get just the domain name so it can be displayed to the user during processing
        parsed_uri = urlparse(url)
        domain = '{uri.netloc}'.format(uri=parsed_uri)
        # Set the filename for the downloaded list
        # Save the file as list.n.domain.name.domains
        # This is useful for debugging as well as keeping the lists out of RAM
        filename = "list." + str(idx) + "." + domain
        try:
            # If there is already an existing file
            if os.path.isfile(filename):
                # Be a respectful netizen by only downloading the list if it is newer by running it though the trasnport_buffer()
                print("Initializing pattern buffer for " + domain + "...")
                pattern_check = transport_buffer(url, filename)
                # If there was not a timestamp from the server, just let the user know and download the list anyway
                if not pattern_check:
                    print("  * Pattern check was inconclusive.")
                    # If it does have a timestamp and thus is older than what is found online, download the list
                    if (pattern_check == True) or (pattern_check == None):
                        print("  * Downloading...")
                        print("")
                        f = urllib2.urlopen(url, timeout = 2)
                        data = f.read()
                        with open(filename, "wb") as code:
                            code.write(data)
                    # Otherwise, do not download so we can respect the list maintiner's bandwidth
                    elif pattern_check == False:
                        print("  * Skipping...")
                        print("")
        except urllib2.URLError, e:
            raise MyException("There was an error: %r" % e)


# Download the blocklists
gravity_well()
