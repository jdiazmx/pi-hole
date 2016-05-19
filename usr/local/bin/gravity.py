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
        print("Local calibration requested.  Scanning...")
    if os.path.isfile(custom_ad_list):
        print("Custom ad lists detected.  Scanning...")

# Be a respectful netizen by only downloading the list if it is newer than the local file
def transport_buffer(url, filename):
    # Get the list
    remote_file = urllib2.urlopen(url)
    try:
        # Get the header from the list so the modification time can be checked
        last_modified = remote_file.headers["Last-Modified"]

        # adblock.gjtech.net returns zero, so this prevents it from diplaying that the pattern check was successful and inconclusive
        if (last_modified == "0"):
            pass
        else:
            print ("  * Pattern check successful.")

        # Convert time to epoch for easy comparision
        temp_time = time.strptime(last_modified, "%a, %d %b %Y %H:%M:%S %Z")
        remote_mtime = time.mktime(temp_time)

        if os.path.isfile(filename):
            # Get the modification time of the local file so it can be comapred with the remote one
            local_mtime = os.path.getmtime(filename)
            print("  * Existing list detected.   (" + str(local_mtime) + ")")

            # Compare the local mtime to the remote mtime.  <------THIS IS BROKEN STILL, but the functionality is there
            # If they are the same, set to False so the list will not be downloaded in grvity_well
            # Since the content is the same, there is no need to re-download it
            if local_mtime > remote_mtime:
                print("  * List is up-to-date.")
                return False
            # Otherwise, the list on the server is newer and should be downloaded (set to True)
            else:
                print("  * Remote list is newer.     (" + str(remote_mtime) + ")")
                return True
        # If there isn't an existing file, it's a new list (or the user deleted the file)
        else:
            return False
            print("  * New list detected.")
    # Retun true to download the list since the mod time was not available
    # This will get the latest file because we don't know if the existing one is out-of-date or not
    except:
        print("  * Pattern check was inconclusive.")
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

        print("Initializing pattern buffer for " + domain + "...")

        # If there is already an existing file
        if os.path.isfile(filename):
            # Be a respectful netizen by only downloading the list if it is newer by running it though the trasnport_buffer()
            pattern_check = transport_buffer(url, filename)
            # If there was not a timestamp from the server, just let the user know and download the list anyway
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

# Download the blocklists
gravity_well()
