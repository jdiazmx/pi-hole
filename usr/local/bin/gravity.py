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
import re
from urlparse import urlparse

##############################
######## FUNCTIONS ###########
def local_calibration():
    if os.path.isfile(pihole_vars.pihole_conf):
        print("Local calibration requested.  Scanning...")
    if os.path.isfile(pihole_vars.custom_ad_list):
        print("Custom ad lists detected.  Scanning...")

# Be a respectful netizen by only downloading the list if it is newer than the local file
def transport_buffer(url, filename):
    # Get the list
    remote_file = urllib2.urlopen(url, timeout=5)
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
            # Otherwise, do not download so we can respect the list maintiner's bandwidth
            elif pattern_check == False:
                print("  * Skipping...")
                print("")

# Finds and aggregats all of the ad list files
def collapse():
    print("Aggregating list of domains...")
    with open(pihole_vars.matter, "wb") as outfile:
        for f in os.listdir(pihole_vars.pihole_dir):
            if f.startswith(pihole_vars.list_prefix):
                with open(f, "rb") as infile:
                    outfile.write(infile.read())

# Line count to display quantity of domains to the user
def particle_density(filename):
    with open(filename) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def matter_and_light():
    print("Getting just the domain names...")
    # Open the aggregated list
    f = open(pihole_vars.matter, "rb")
    # Make a new file to put just the domain names in
    with open(pihole_vars.and_light, "wb") as and_light:
        # For each line from the aggregated list,
        for line in f.readlines():
            # Find all the domains (P.S. I have no idea how the regex works, but it seems to)
            line = re.findall(r'(\S+)', line)
            # If there is not an entry, skip it
            if not line:
                pass
            # Also pass if there is a comment
            elif "#" in line[0]:
                pass
            # Also print the second field if the line starts with 127.0.0.1
            elif (line[0] == "127.0.0.1"):
                and_light.write("%s\n" % line[1])
            # After all that, write the first field, which should be the domain name
            else:
                and_light.write("%s\n" % line[0])
    print(str(particle_density(pihole_vars.event_horizon)) + " domains exist before refinement.")

def event_horizon():
    print("Sorting and removing duplicates...")
    # Open the list of just domain names
    f = open(pihole_vars.and_light, "rb")
    # Keep track of the lines that already exist
    lines_seen = set()
    # Open the file the sorted list will go into
    outfile = open(pihole_vars.event_horizon, "wb")
    # For each line in the domain list,
    for line in open(pihole_vars.and_light, "rb"):
        # If the line is not a duplicate, write it to the new file
        if line not in lines_seen:
            lines_seen.add(line)
    # Sort the list for readability
    outfile.writelines(sorted(lines_seen))
    print(str(particle_density(pihole_vars.event_horizon)) + " domains trapped in the event horizon.")

# Download the blocklists
gravity_well()

# Find all of the downloaded lists
collapse()

# Extract just the domain names
matter_and_light()

# Sort and remove duplicates
event_horizon()
