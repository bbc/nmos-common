import socket
from zeroconf import Zeroconf
from nmoscommon.logger import Logger
from .mdnsExceptions import InterfaceNotFoundException


class MDNSInterface(object):

    def __init__(self, interfaceIp):
        self.logger = Logger('MDNSInterface')
        self.ip = interfaceIp
        self._establish_interface()
        self.advertisedServices = {}

    def _establish_interface(self):
        try:
            self.zeroconf = Zeroconf([self.ip])
        except socket.error:
            msg = "Could not find interface with IP {}".format(self.ip)
            self.logger.writeError(msg)
            raise InterfaceNotFoundException(msg)

    def registerService(self, info):
        self.zeroconf.register_service(info)

    def unregisterService(self, info):
        self.zeroconf.unregister_service(info)

    def close(self):
        self.zeroconf.close()
