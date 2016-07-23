#!/usr/bin/env python3
# Copyright (c) 2016 Jacob Salmela
# Pi-hole: a DNS based ad-blocker [https://www.pi-hole.net]
#
# Whitelist domains from the gravity list
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


"""Whitelist one or more domains from Pi-hole's ad-blocking gravity

Usage:
    pihole whitelist list
    pihole whitelist [-d] [-f] <domains>...

Commands:
    list                List the domains

Options:
    -d --delete         Delete the domain(s)
    -f --force          Force reload DNS, even if no changes have been made"""


# IMPORTS


import pihole_vars
from docopt import docopt


# SCRIPT


def main(argv):
    if argv is None:
        args = docopt(__doc__)
    else:
        args = docopt(__doc__, argv=argv)

    print("Loading Pi-hole instance...")
    pihole = pihole_vars.Pihole()

    if args["list"]:
        whitelist = pihole.get_whitelist()

        if len(whitelist) == 0:
            print("Your whitelist is empty!")
        else:
            for i, domain in enumerate(pihole.get_whitelist(), start=1):
                print(str(i) + ") " + domain)
    else:
        domains = args["<domains>"]
        delete = args["--delete"]
        force = args["--force"]
        changed = []

        for domain in domains:
            if not delete:
                if domain in pihole.get_whitelist():
                    print(domain + " is already in the whitelist!")
                    continue

                print("Adding " + domain + " to the whitelist")
                changed.append(pihole.add_whitelist(domain))
                print("    Done!")
            else:
                if domain not in pihole.get_whitelist():
                    print(domain + " is not in the whitelist!")
                    continue

                print("Removing " + domain + " from the whitelist")
                changed.append(pihole.remove_whitelist(domain))
                print("    Done!")

        # Regenerate and reload DNS only if something changed, or we're forced to
        if True in changed or force:
            print("Recalibrating gravity...")
            pihole.export_hosts()
            pihole_vars.restart_gravity()
            print("Done!")
        else:
            print("Gravity has not been altered")


if __name__ == "__main__":
    main(None)
