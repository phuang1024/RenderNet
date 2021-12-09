#
#  Renderfarm
#  Blender rendering service.
#  Copyright Patrick Huang 2021
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import os
import json
from subprocess import Popen, PIPE, DEVNULL

PARENT = os.path.dirname(os.path.abspath(__file__))


class Server:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password

    def system(self, command):
        """
        Returns the exit code.
        """
        args = ["sshpass", "-p", self.password, "ssh", f"{self.username}@{self.ip}", *command.split()]
        proc = Popen(args, stdin=DEVNULL, stdout=PIPE, stderr=PIPE)
        proc.wait()
        return proc.returncode


def main():
    with open(os.path.join(PARENT, "servers.json"), "r") as fp:
        data = json.load(fp)

    servers = []
    for server in data["servers"]:
        servers.append(Server(server["ip"], server["username"], server["password"]))

    print(servers[0].system("rm a"))


main()
