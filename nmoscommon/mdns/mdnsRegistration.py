from zeroconf import ServiceInfo
from socket import inet_aton


class MDNSRegistration(object):

    def __init__(self, interfaces, name, regtype, port, txtRecord=None):
        if not txtRecord:
            txtRecord = {}
        self.name = name.replace(".", "-")
        self.regtype = regtype
        self.port = port
        self.txtRecord = txtRecord
        self.interfaces = interfaces
        self.info = {}

    def register(self):
        nameList = self._makeNamesUnique()
        regtype = self.regtype + ".local."
        for interface in self.interfaces:
            name = nameList[interface.ip] + "." + self.regtype + ".local."
            self.info[interface.ip] = ServiceInfo(
                type_=regtype,
                name=name,
                port=self.port,
                properties=self.txtRecord,
                address=inet_aton(interface.ip)
            )
            interface.registerService(self.info[interface.ip])

    def _makeNamesUnique(self):
        if len(self.interfaces) == 1:
            return {self.interfaces[0].ip: self.name}
        else:
            nameList = {}
            for interface in self.interfaces:
                noDotIp = interface.ip.replace(".", "-")
                nameList[interface.ip] = self.name + "_{}".format(noDotIp)
            return nameList

    def unRegister(self):
        for interface in self.interfaces:
            interface.unregisterService(self.info[interface.ip])
