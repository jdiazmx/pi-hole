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


# IMPORTS


from pihole import Pihole, restart_gravity
from docopt import docopt


# SCRIPT


whitelist = """Whitelist one or more domains from Pi-hole's ad-blocking gravity

Usage:
    pihole whitelist list
    pihole whitelist [-d] [-f] <domains>...

Commands:
    list                List the domains

Options:
    -d --delete         Delete the domain(s)
    -f --force          Force reload DNS, even if no changes have been made"""

blacklist = """Blacklist one or more domains to Pi-hole's ad-blocking gravity

Usage:
    pihole blacklist list
    pihole blacklist [-d] [-f] <domains>...

Commands:
    list                List the domains

Options:
    -d --delete         Delete the domain(s)
    -f --force          Force reload DNS, even if no changes have been made"""


def get_list(is_whitelist, pihole):
    return pihole.get_whitelist() if is_whitelist else pihole.get_blacklist()


def main(argv, is_whitelist):
    global whitelist, blacklist
    if is_whitelist:
        args = docopt(whitelist, argv=argv)
    else:
        args = docopt(blacklist, argv=argv)

    print("Loading Pi-hole instance...")
    pihole = Pihole()
    list_type = "whitelist" if is_whitelist else "blacklist"

    if args["list"]:
        l = get_list(is_whitelist, pihole)

        if len(l) == 0:
            print("Your " + list_type + " is empty!")
        else:
            for i, domain in enumerate(l, start=1):
                print(str(i) + ") " + domain)
    else:
        domains = args["<domains>"]
        delete = args["--delete"]
        force = args["--force"]
        changed = []

        for domain in domains:
            if not delete:
                if domain in get_list(is_whitelist, pihole):
                    print(domain + " is already in the " + list_type + "!")
                    continue

                print("Adding " + domain + " to the " + list_type)

                if is_whitelist:
                    changed.append(pihole.add_whitelist(domain))
                else:
                    changed.append(pihole.add_blacklist(domain))

                print("    Done!")
            else:
                if domain not in get_list(is_whitelist, pihole):
                    print(domain + " is not in the " + list_type + "!")
                    continue

                print("Removing " + domain + " from the " + list_type)

                if is_whitelist:
                    changed.append(pihole.remove_whitelist(domain))
                else:
                    changed.append(pihole.remove_blacklist(domain))

                print("    Done!")

        # Regenerate and reload DNS only if something changed, or we're forced to
        if True in changed or force:
            print("Recalibrating gravity...")
            pihole.export_hosts()
            restart_gravity()
            print("    Done!")
        else:
            print("Gravity has not been altered")
