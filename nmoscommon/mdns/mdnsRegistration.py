from zeroconf import ServiceInfo


class MDNSRegistration(object):

    def __init__(self, zeroconf, name, regtype, port, txtRecord={}):
        self.name = name
        self.regtype = regtype
        self.port = port
        self.txtRecord = txtRecord
        self.zeroconf = zeroconf
        self.info = None

    def register(self):
        self.info = ServiceInfo(
            type=self.regtype + ".local.",
            name=self.name,
            port=self.port,
            properties=self.txtRecord
        )
        self.zeroconf.register_service(self.info)

    def unRegister(self):
        self.zeroconf.unregister_service(self.info)
