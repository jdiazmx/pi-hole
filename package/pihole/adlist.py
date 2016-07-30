# Copyright (c) 2016 Jacob Salmela
# Pi-hole: a DNS based ad-blocker [https://www.pi-hole.net]
#
# Add/Remove ad-lists
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


"""Add/Remove ad-lists

Usage:
    pihole adlist list
    pihole adlist [-d] <URIs>...

Commands:
    list            List the ad-lists

Options:
    -d --delete     Delete ad-list(s)"""


# IMPORTS


from pihole import Pihole
from docopt import docopt


# SCRIPT


def main(argv):
    args = docopt(__doc__, argv)

    print("Loading Pi-hole instance...")
    pihole = Pihole()
    changed = False

    if args["list"]:
        lists = pihole.get_list_uris()

        if len(lists) == 0:
            print("You have no lists (that's a bad thing)!")
        else:
            for i, l in enumerate(lists, start=1):
                print(str(i) + ") " + l)
    else:
        lists = args["<URIs>"]
        delete = args["--delete"]

        for l in lists:
            if not delete:
                # Only add if it's not there
                if l in pihole.get_list_uris():
                    print("This list is already added: " + l)
                    continue

                print("Adding " + l)
                pihole.add_list(l)
                changed = True
                print("    Done!")
            else:
                # Only delete if it's there
                if l not in pihole.get_list_uris():
                    print("This list is not in the list of lists: " + l)
                    continue

                print("Removing " + l)
                pihole.remove_list(l)
                changed = True
                print("    Done!")

        if changed:
            print('You should run "pihole gravity" now to refresh gravity')
        else:
            print("Gravity has not been altered")
