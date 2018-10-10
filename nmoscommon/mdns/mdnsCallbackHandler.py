class MDNSAdvertisementCallbackHandler(object):

    def __init__(self, callback, registration):
        self.callback = callback
        self.registration = registration

    def entryColission(self):
        if self.callback is not None:
            self.callback(self._buildMessage("collision"))

    def entryEstablisted(self):
        if self.callback is not None:
            self.callback(self._buildMessage("established"))

    def entryFailed(self):
        if self.callback is not None:
            self.callback(self._buildMessage("failed"))

    def _buildMessage(self, action):
        return {
                "action": action,
                "name": self.registration.name,
                "regtype": self.registration.regtype,
                "port": self.registration.port,
                "txtRecord": self.registration.txtRecord
                }
