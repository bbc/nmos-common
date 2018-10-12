from .mdnsExceptions import ServiceAlreadyExistsException


class MDNSRegistrationController(object):

    def __init__(self):
        self.registrations = {}

    def addRegistration(self, registration):
        name = registration.name
        regtype = registration.regtype
        if registration.regtype in self.registrations:
            if registration.name in self.registrations[regtype]:
                raise ServiceAlreadyExistsException()
        else:
            self.registrations[regtype] = {}
        self.registrations[regtype][name] = registration
        registration.register()

    def removeRegistration(self, name, regtype):
        self.registrations[regtype].pop(name).close()
        if self.registrations[regtype] == {}:
            self.registrations.pop(regtype)

    def close(self):
        for regtype in self.registrations:
            for name in self.registrations[regtype]:
                self.registrations[regtype][name].unRegister()
        self.registrations = {}
