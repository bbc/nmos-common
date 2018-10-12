import netifaces
from .mdnsInterface import MDNSInterface


class MDNSInterfaceController(object):

    def __init__(self):
        self.interfaces = {}
        self.defaultInterface = self._findDefaultInterface()

    def _findDefaultInterface(self):
        defaultGateways = netifaces.gateways()
        defaultInterfaceName = defaultGateways[netifaces.AF_INET][0][1]
        defaultInterfaceDetails = netifaces.ifaddresses(defaultInterfaceName)
        defaultInterfaceIp = defaultInterfaceDetails[netifaces.AF_INET][0]['addr']
        return self.addInterface(defaultInterfaceIp)

    def addInterface(self, ip):
        if ip not in self.interfaces.keys():
            self.interfaces[ip] = MDNSInterface(ip)
        return self.interfaces[ip]

    def getInterfaces(self, interfaceIps):
        if interfaceIps == []:
            return [self.defaultInterface]
        else:
            interfaceList = []
            for ip in interfaceIps:
                interfaceList.append(self.addInterface(ip))
            return interfaceList

    def close(self):
        for key, interface in self.interfaces.items():
            interface.close()
