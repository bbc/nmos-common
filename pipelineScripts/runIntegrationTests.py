#!/bin/python

import re
from subprocess import call


def findPortLines(inputString):
    pattern = r"^[0-9]*,[a-z 0-9]*,forwarded_port,([0-9]*),([0-9]*)$"
    portLines = {}
    for line in inputString:
        match = re.match(pattern, line)
        if match:
            portLines[match.group(1)] = match.group(2)
            print match.group()
            print match.group(1)
            print match.group(2)
    return portLines


node_ports = call("(cd nmos-joint-ri/Vagrant; vagrant port node --machine-readable)", shell=True)
regquery_ports = call("(cd nmos-joint-ri/Vagrant; vagrant port node --machine-readable)", shell=True)

print(findPortLines(node_ports))
print(findPortLines(regquery_ports))
