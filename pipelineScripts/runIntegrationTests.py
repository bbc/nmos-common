#!/bin/python

from subprocess import call

node_ports = call("(cd nmos-joint-ri/Vagrant; vagrant port node --machine-readable)", shell=True)
regquery_ports = call("(cd nmos-joint-ri/Vagrant; vagrant port node --machine-readable)", shell=True)

print(node_ports)
print(regquery_ports)
