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
    pihole whitelist [-d] [-f] [-e] <domains>...

Commands:
    list                List the domains

Options:
    -d --delete         Delete the domain(s)
    -f --force          Force reload DNS, even if no changes have been made
    -e --errors-only    Only output status codes"""


# IMPORTS


import pihole_vars
from docopt import docopt


# SCRIPT


errors = False
codes = []


def log(output):
    if not errors:
        print(output)


def log_code(domain, code):
    codes.append({
        "domain": domain,
        "code": code
    })


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
        global errors
        domains = args["<domains>"]
        delete = args["--delete"]
        force = args["--force"]
        errors = args["--errors-only"]
        changed = []

        for domain in domains:
            if not delete:
                if domain in pihole.get_whitelist():
                    log(domain + " is already in the whitelist!")
                    log_code(domain, pihole_vars.error_codes["domain_already_exists"])
                    continue

                log("Adding " + domain + " to the whitelist")
                changed.append(pihole.add_whitelist(domain))
                log("    Done!")
                log_code(domain, pihole_vars.error_codes["success"])
            else:
                if domain not in pihole.get_whitelist():
                    log(domain + " is not in the whitelist!")
                    log_code(domain, pihole_vars.error_codes["domain_does_not_exist"])
                    continue

                log("Removing " + domain + " from the whitelist")
                changed.append(pihole.remove_whitelist(domain))
                log("    Done!")
                log_code(domain, pihole_vars.error_codes["success"])

        # Regenerate hosts list
        log("Recalibrating gravity...")
        pihole.export_hosts()

        # Reload DNS only if something changed, or we're forced to
        if True in changed or force:
            log("Restarting gravity...")
            pihole_vars.restart_gravity()
            log("Done!")
            pass
        else:
            log("Gravity has not been altered")

        # Print codes if asked (lists of numbers in Python print the same as JSON)
        if errors:
            print(codes)


if __name__ == "__main__":
    main(None)
